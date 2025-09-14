import asyncio, websockets, json, os, uuid
from channel import Channel
from modules.crypto_utils import AESHandler
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

HOST, PORT = "127.0.0.1", 8765
ID_FILE = "./storage/client_id"
KEY_DIR = "./storage/keys"
os.makedirs(KEY_DIR, exist_ok=True)

PRIV_FILE = f"{KEY_DIR}/client_rsa_private.pem"
PUB_FILE = f"{KEY_DIR}/client_rsa_public.pem"

if not os.path.exists(PRIV_FILE):
    priv = rsa.generate_private_key(65537, 2048)
    pub = priv.public_key()
    with open(PRIV_FILE, "wb") as f: f.write(priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()
    ))
    with open(PUB_FILE, "wb") as f: f.write(pub.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    ))

with open(PRIV_FILE, "rb") as f: CLIENT_PRIV = serialization.load_pem_private_key(f.read(), None)

SERVER_PUB_FILE = f"{KEY_DIR}/server_rsa_public.pem"
with open(SERVER_PUB_FILE, "rb") as f: SERVER_PUB = f.read()

class ClientConnection:
    def __init__(self):
        self.ws = None
        self.channel = None
        self.client_id = None
        self.inbox = asyncio.Queue()
        self.receive_task = None

    async def connect(self):
        self.ws = await websockets.connect(f"ws://{HOST}:{PORT}")
        self.channel = Channel(self.ws, SERVER_PUB)
        await self.channel.handshake()

        self.client_id = open(ID_FILE).read().strip() if os.path.exists(ID_FILE) else str(uuid.uuid4())

        pub_bytes = CLIENT_PRIV.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()

        signature = CLIENT_PRIV.sign(
            self.client_id.encode(),
            padding.PSS(padding.MGF1(hashes.SHA256()), padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )

        payload = {"client_id": self.client_id, "signature": signature.hex(), "pub_key": pub_bytes}
        n, c = AESHandler.encrypt(self.channel.aesgcm, json.dumps(payload))
        await self.ws.send(json.dumps({"nonce": n.hex(), "ciphertext": c.hex()}))

        # Challenge-response dal server
        challenge_msg = await self.ws.recv()
        challenge_data = json.loads(challenge_msg)
        challenge = AESHandler.decrypt(
            self.channel.aesgcm,
            bytes.fromhex(challenge_data["nonce"]),
            bytes.fromhex(challenge_data["ciphertext"])
        )
        challenge_bytes = bytes.fromhex(challenge)

        # Firma del challenge
        sig = CLIENT_PRIV.sign(
            challenge_bytes,
            padding.PSS(padding.MGF1(hashes.SHA256()), padding.PSS.MAX_LENGTH),
            hashes.SHA256()
        )
        n, c = AESHandler.encrypt(self.channel.aesgcm, sig.hex())
        await self.ws.send(json.dumps({"nonce": n.hex(), "ciphertext": c.hex()}))

        # handshake completato
        self.receive_task = asyncio.create_task(self.channel.receive_loop(self.on_message, self.on_disconnect))
        print(f"[*] Connected as {self.client_id}")


    async def send_message_to(self, target_id, text):
        msg = {"target": target_id, "text": text}
        await self.channel.send(json.dumps(msg))

    async def receive_message(self):
        return await self.inbox.get()

    def on_message(self, message):
        try:
            data = json.loads(message)
            self.inbox.put_nowait((data.get("sender", "unknown"), data.get("text", message)))
        except: print(message)

    def on_disconnect(self): print("[*] Disconnected from server")

    async def close(self):
        if self.receive_task:
            self.receive_task.cancel()
            try: await self.receive_task
            except asyncio.CancelledError: pass
        if self.ws: await self.ws.close()