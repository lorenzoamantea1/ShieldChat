import asyncio, json, uuid
from collections import deque
from modules.crypto_utils import AESHandler, RSAHandler
from cryptography.hazmat.primitives import serialization
import os

CLIENT_KEYS_FILE = "./storage/client_keys.json"

class ServerConnection:
    def __init__(self, ws, server_rsa, clients_map):
        self.ws = ws
        self.server_rsa = server_rsa
        self.aesgcm = None
        self.clients_map = clients_map
        self.client_id = None
        self.client_pub = None
        self.used_nonces = []
        self.client_keys = self.load_client_keys()

    def load_client_keys(self):
        if os.path.exists(CLIENT_KEYS_FILE):
            with open(CLIENT_KEYS_FILE, "r") as f:
                return json.load(f)
        return {}

    def save_client_keys(self):
        os.makedirs(os.path.dirname(CLIENT_KEYS_FILE), exist_ok=True)
        with open(CLIENT_KEYS_FILE, "w") as f:
            json.dump(self.client_keys, f)

    async def handshake(self):
        from modules.protocol import Handshake

        h = Handshake(self.ws, rsa_priv=self.server_rsa.priv, rsa_pub=self.server_rsa.pub, is_server=True)
        self.aesgcm = await h.run()

        msg = await self.ws.recv()
        data = json.loads(msg)
        payload = json.loads(AESHandler.decrypt(self.aesgcm, bytes.fromhex(data["nonce"]), bytes.fromhex(data["ciphertext"])))
        proposed_id = payload["client_id"]
        signature = bytes.fromhex(payload["signature"])
        pub_key_str = payload["pub_key"]

        if proposed_id in self.client_keys:
            self.client_pub = serialization.load_pem_public_key(self.client_keys[proposed_id].encode())
        else:
            self.client_pub = serialization.load_pem_public_key(pub_key_str.encode())
            self.client_keys[proposed_id] = pub_key_str
            self.save_client_keys()

        if not RSAHandler.verify(self.client_pub, proposed_id.encode(), signature):
            raise ValueError("Invalid client signature!")

        if proposed_id in self.clients_map:
            raise ValueError("Client ID already in use!")

        challenge = os.urandom(16)
        n, c = AESHandler.encrypt(self.aesgcm, challenge.hex())
        await self.ws.send(json.dumps({"nonce": n.hex(), "ciphertext": c.hex()}))

        resp_msg = await self.ws.recv()
        resp_data = json.loads(resp_msg)
        resp_plain = AESHandler.decrypt(self.aesgcm, bytes.fromhex(resp_data["nonce"]), bytes.fromhex(resp_data["ciphertext"]))
        resp_sig = bytes.fromhex(resp_plain)

        if not RSAHandler.verify(self.client_pub, challenge, resp_sig):
            raise ValueError("Challenge failed! Invalid client signature.")

        self.client_id = proposed_id
        self.clients_map[self.client_id] = self
        print(f"[*] Handshake complete, client_id: {self.client_id}")


    async def handle_messages(self):
        try:
            async for msg in self.ws:
                await self.process_message(msg)
        except Exception as e: print(f"[!] Error {self.client_id}: {e}")
        finally:
            if self.client_id in self.clients_map: del self.clients_map[self.client_id]
            await self.ws.close()
            print(f"[*] Client {self.client_id} disconnected")

    async def process_message(self, message):
        try:
            data = json.loads(message)
            nonce, ct = bytes.fromhex(data.get("nonce", "")), bytes.fromhex(data.get("ciphertext", ""))
            if (self.client_id, nonce) in self.used_nonces: 
                return
            self.used_nonces.append((self.client_id, nonce))

            plaintext = AESHandler.decrypt(self.aesgcm, nonce, ct)
            payload = json.loads(plaintext)
            target_id, text = payload.get("target"), payload.get("text")

            if target_id in self.clients_map:
                tconn = self.clients_map[target_id]
                n, c = AESHandler.encrypt(tconn.aesgcm, json.dumps({"text": text, "sender": self.client_id}))
                await tconn.ws.send(json.dumps({"nonce": n.hex(), "ciphertext": c.hex()}))
        except Exception as e: 
            print(f"[!] Error {self.client_id}: {e}")
            