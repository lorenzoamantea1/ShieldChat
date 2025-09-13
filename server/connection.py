import json
import time
from collections import deque
from modules.keys import RSAKey
from modules.protocol import Handshake
from modules.crypto_utils import AESHandler

class ServerConnection:
    def __init__(self, websocket, key_dir, clients_map, nonce_history_size=1000):
        self.ws = websocket
        self.server_rsa = RSAKey(key_dir)
        self.used_nonces = deque(maxlen=nonce_history_size)
        self.aesgcm = None
        self.counter = 1
        self.client_id = None
        self.clients_map = clients_map

    async def handshake(self):
        handshake = Handshake(
            self.ws,
            rsa_priv=self.server_rsa.priv,
            rsa_pub=self.server_rsa.pub,
            is_server=True
        )
        self.aesgcm = await handshake.run()
        print(f"[*] Handshake complete with client")

    async def handle_messages(self):
        try:
            msg = await self.ws.recv()
            data = json.loads(msg)
            self.client_id = AESHandler.decrypt(
                self.aesgcm,
                bytes.fromhex(data["nonce"]),
                bytes.fromhex(data["ciphertext"])
            )
            self.clients_map[self.client_id] = self
            print(f"[*] Client connected: {self.client_id}")
        except Exception as e:
            print(f"[!] Error receiving client ID: {e}")
            await self.ws.close()
            return

        try:
            async for message in self.ws:
                await self.process_message(message)
        except:
            print(f"[*] Client {self.client_id} disconnected")
            if self.client_id in self.clients_map:
                del self.clients_map[self.client_id]

    async def process_message(self, message):
        try:
            data = json.loads(message)
            nonce = bytes.fromhex(data["nonce"])
            ct = bytes.fromhex(data["ciphertext"])

            if nonce in self.used_nonces:
                print(f"[!] Replay attack detected, ignoring message #{self.counter}")
                return
            self.used_nonces.append(nonce)

            plaintext = AESHandler.decrypt(self.aesgcm, nonce, ct)

            try:
                try:
                    payload = json.loads(plaintext)
                except json.JSONDecodeError:
                    print(f"[!] Invalid JSON from {self.client_id}, closing connection")
                    await self.ws.close()
                    return
                target_id = payload.get("target")
                text = payload.get("text")
                sender = payload.get("sender","unknown")
                if target_id and target_id in self.clients_map:
                    target_conn = self.clients_map[target_id]
                    forward_payload = json.dumps({
                        "text": text,
                        "sender": self.client_id
                    })
                    n, c = AESHandler.encrypt(target_conn.aesgcm, forward_payload)
                    await target_conn.ws.send(json.dumps({"nonce": n.hex(), "ciphertext": c.hex()}))
                    print(f"[*] Forwarded message from {self.client_id} to {target_id}")
                    return
            except Exception as e:
                pass

            reply_text = f"Server received: {plaintext}"
            nonce_reply, ct_reply = AESHandler.encrypt(self.aesgcm, reply_text)
            await self.ws.send(json.dumps({"nonce": nonce_reply.hex(), "ciphertext": ct_reply.hex()}))
            self.counter += 1
        except Exception as e:
            print(f"[!] Message processing error: {e}")