from cryptography.hazmat.primitives import serialization

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
