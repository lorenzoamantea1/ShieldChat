import json
from modules.keys import ServerRSA
from modules.protocol import Handshake
from modules.crypto_utils import AESHandler

class Channel:
    def __init__(self, websocket, server_pub):
        self.ws = websocket
        self.server_rsa = ServerRSA(server_pub)
        self.aesgcm = None

    async def handshake(self):
        handshake = Handshake(
            self.ws,
            rsa_priv=None,
            rsa_pub=None,
            peer_rsa_pub=self.server_rsa.get_pub(),
            is_server=False
        )
        self.aesgcm = await handshake.run()

    async def send(self, text):
        nonce, ct = AESHandler.encrypt(self.aesgcm, text)
        await self.ws.send(json.dumps({"nonce": nonce.hex(), "ciphertext": ct.hex()}))

    async def receive_loop(self, on_message, on_disconnect):
        try:
            async for msg in self.ws:
                data = json.loads(msg)
                plaintext = AESHandler.decrypt(self.aesgcm, bytes.fromhex(data["nonce"]), bytes.fromhex(data["ciphertext"]))
                on_message(plaintext)
        except:
            on_disconnect()
