import os
import uuid
import json
import asyncio
import websockets
from channel import Channel

HOST = "localhost"
PORT = 8765
ID_FILE = "./.id"
SERVER_PUB = "./keys/server_rsa_public.pem"
with open(SERVER_PUB) as f:
    SERVER_PUB_PEM = f.read().encode()

def getClientId():
    return str(uuid.uuid4())

class ClientConnection:
    def __init__(self, host=HOST, port=PORT, server_pub=SERVER_PUB_PEM):
        self.host = host
        self.port = port
        self.client_id = getClientId()
        self.ws = None
        self.channel = None
        self.receive_task = None
        self.inbox = asyncio.Queue()

    async def connect(self):
        self.ws = await websockets.connect(
            f"ws://{self.host}:{self.port}",
            ping_interval=15,
            ping_timeout=30
        )
        self.channel = Channel(self.ws, SERVER_PUB_PEM)
        await self.channel.handshake()
        await self.channel.send(self.client_id)
        self.receive_task = asyncio.create_task(
            self.channel.receive_loop(self.on_message, self.on_disconnect)
        )
        print(f"[*] Connected as {self.client_id}")

    async def send_message_to(self, target_id, text):
        msg = {
            "target": target_id,
            "text": text,
            "sender": self.client_id
        }
        await self.channel.send(json.dumps(msg))

    def on_message(self, message):
        try:
            data = json.loads(message)

            sender = data.get("sender", "unknown")
            text = data.get("text", message)
            self.inbox.put_nowait((sender, text))
        except Exception:
            print(f"[Server/Other] {message}")

    def on_disconnect(self):
        print("[*] Disconnected from server")

    async def receive_message(self):
        return await self.inbox.get()

    async def close(self):
        if self.receive_task:
            self.receive_task.cancel()
            try:
                await self.receive_task
            except asyncio.CancelledError:
                pass
        if self.ws:
            await self.ws.close() 