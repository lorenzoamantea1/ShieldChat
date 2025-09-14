from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import os

class ServerRSA:
    """Client-side access to server's RSA public key"""

    def __init__(self, pem_bytes: bytes):
        self.pub = serialization.load_pem_public_key(pem_bytes)

    def get_pub(self):
        return self.pub

    def serialize(self):
        return self.pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
class RSAKey:
    """Server RSA key pair"""
    def __init__(self, priv, pub):
        self.priv = priv
        self.pub = pub

    @classmethod
    def generate(cls, bits=2048):
        priv = rsa.generate_private_key(public_exponent=65537, key_size=bits)
        pub = priv.public_key()
        return cls(priv, pub)

    def save(self, priv_path, pub_path):
        with open(priv_path, "wb") as f:
            f.write(self.priv.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption()
            ))
        with open(pub_path, "wb") as f:
            f.write(self.pub.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

    @classmethod
    def load(cls, priv_path, pub_path):
        from cryptography.hazmat.primitives import serialization
        with open(priv_path, "rb") as f:
            priv = serialization.load_pem_private_key(f.read(), password=None)
        with open(pub_path, "rb") as f:
            pub = serialization.load_pem_public_key(f.read())
        return cls(priv, pub)