import json
from .crypto_utils import X25519Key, AESHandler, RSAHandler

class Handshake:
    """Secure handshake using ephemeral X25519 signed by server RSA"""

    def __init__(self, ws, rsa_priv, rsa_pub, peer_rsa_pub=None, is_server=False):
        self.ws = ws
        self.rsa_priv = rsa_priv
        self.rsa_pub = rsa_pub
        self.peer_rsa_pub = peer_rsa_pub
        self.is_server = is_server
        self.aesgcm = None

    async def run(self):
        if self.is_server:
            # Server: ephemeral X25519, sign, send
            xkey = X25519Key()
            sig = RSAHandler.sign(self.rsa_priv, xkey.pub_bytes)
            await self.ws.send(json.dumps({"xpub": xkey.pub_bytes.hex(), "sig": sig.hex()}))

            # Receive ephemeral X25519 from client
            peer_data = json.loads(await self.ws.recv())
            peer_xpub = bytes.fromhex(peer_data["xpub"])
        else:
            # Client: receive server ephemeral key + signature
            peer_data = json.loads(await self.ws.recv())
            peer_xpub = bytes.fromhex(peer_data["xpub"])
            peer_sig = bytes.fromhex(peer_data["sig"])
            if not RSAHandler.verify(self.peer_rsa_pub, peer_xpub, peer_sig):
                raise ValueError("Invalid server signature!")

            # Client generates ephemeral X25519 and sends to server
            xkey = X25519Key()
            await self.ws.send(json.dumps({"xpub": xkey.pub_bytes.hex()}))

        # Derive shared AES key
        shared = xkey.exchange(X25519Key.load_pub(peer_xpub))
        self.aesgcm = AESHandler.make(AESHandler.derive_key(shared))
        return self.aesgcm
