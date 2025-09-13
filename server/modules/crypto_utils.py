from cryptography.hazmat.primitives.asymmetric import x25519, padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

class X25519Key:
    """Ephemeral X25519 key"""

    def __init__(self):
        self.priv = x25519.X25519PrivateKey.generate()
        self.pub_bytes = self.priv.public_key().public_bytes_raw()

    @staticmethod
    def load_pub(raw_bytes):
        return x25519.X25519PublicKey.from_public_bytes(raw_bytes)

    def exchange(self, peer_pub):
        return self.priv.exchange(peer_pub)

class RSAHandler:
    """Sign and verify data using RSA"""

    @staticmethod
    def sign(priv, data: bytes) -> bytes:
        return priv.sign(
            data,
            padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )

    @staticmethod
    def verify(pub, data: bytes, sig: bytes) -> bool:
        try:
            pub.verify(
                sig, data,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False

class AESHandler:
    """AES-GCM encryption/decryption with random nonce"""

    @staticmethod
    def derive_key(shared_secret: bytes) -> bytes:
        return HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=b"shield-chat").derive(shared_secret)

    @staticmethod
    def make(key: bytes) -> AESGCM:
        return AESGCM(key)

    @staticmethod
    def encrypt(aesgcm, text: str) -> tuple[bytes, bytes]:
        """
        Encrypt text.
        Returns: (nonce, ciphertext)
        """
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, text.encode(), None)
        return nonce, ct

    @staticmethod
    def decrypt(aesgcm, nonce: bytes, blob: bytes) -> str:
        return aesgcm.decrypt(nonce, blob, None).decode()
