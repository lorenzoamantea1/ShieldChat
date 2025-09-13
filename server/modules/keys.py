from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import os

class RSAKey:
    """Server RSA key pair"""

    def __init__(self, dirpath=None):
        self.priv = None
        self.pub = None
        self.dirpath = dirpath
        if dirpath:
            self.load_or_generate(dirpath)
        else:
            self.generate()

    def generate(self):
        self.priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.pub = self.priv.public_key()

    def load_or_generate(self, dirpath):
        priv_path = os.path.join(dirpath, "rsa_private.pem")
        pub_path = os.path.join(dirpath, "rsa_public.pem")
        if os.path.exists(priv_path) and os.path.exists(pub_path):
            with open(priv_path, "rb") as f:
                self.priv = serialization.load_pem_private_key(f.read(), password=None)
            with open(pub_path, "rb") as f:
                self.pub = serialization.load_pem_public_key(f.read())
        else:
            self.generate()
            os.makedirs(dirpath, exist_ok=True)
            with open(priv_path, "wb") as f:
                f.write(self.priv.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            with open(pub_path, "wb") as f:
                f.write(self.pub.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))

    def serialize_pub(self):
        return self.pub.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

    @staticmethod
    def deserialize_pub(pem_bytes):
        return serialization.load_pem_public_key(pem_bytes)