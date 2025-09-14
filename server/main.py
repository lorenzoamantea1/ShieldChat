import asyncio
import websockets
from connection import ServerConnection
from modules.keys import RSAKey
from cryptography.hazmat.primitives import serialization

HOST = "0.0.0.0"
PORT = 8765
KEY_DIR = "./storage/keys"
KEEPALIVE_INTERVAL = 15
NONCE_HISTORY_SIZE = 1000

class WebSocketServer:
    def __init__(self, host, port, server_rsa, keepalive, nonce_history_size=1000):
        self.host = host
        self.port = port
        self.server_rsa = server_rsa
        self.keepalive = keepalive
        self.nonce_history_size = nonce_history_size
        self.clients_map = {}

    async def handle_client(self, ws):

        connection = ServerConnection(ws, self.server_rsa, self.clients_map)
        await connection.handshake()
        await connection.handle_messages()
        if connection.client_id in self.clients_map:
            del self.clients_map[connection.client_id]
        print(f"[*] Connection with client {connection.client_id} closed")

    async def start(self):
        print(f"[*] WebSocket server running on {self.host}:{self.port}")
        async with websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=self.keepalive,
            ping_timeout=self.keepalive*2
        ):
            await asyncio.Future()

if __name__ == "__main__":
    server_rsa = RSAKey(KEY_DIR)
    server_rsa_key = server_rsa.pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    print(f"[*] Server RSA public key:\n{server_rsa_key.decode()}")
    server = WebSocketServer(
        host=HOST,
        port=PORT,
        server_rsa=server_rsa,
        keepalive=KEEPALIVE_INTERVAL,
        nonce_history_size=NONCE_HISTORY_SIZE
    )
    asyncio.run(server.start())