import asyncio
from connection import ClientConnection
import time
import os

class Client:
    def __init__(self):
        self.selectedChat = None
        self.inbox = {}
        self.clientConnect = ClientConnection()
        asyncio.run(self.main())

    def log(self, msg):
        print(f"[{time.strftime('%H:%M:%S')}] {msg}")

    async def async_input(self, prompt):
        return await asyncio.to_thread(input, prompt)

    async def display(self):
        os.system("clear")
        print(self.selectedChat)


        if self.selectedChat in self.inbox:
            for msg in self.inbox[self.selectedChat]:
                print(msg)

        print("> ", end="", flush=True)

    async def receive_messages(self):
        while True:
            try:
                sender, msg = await self.clientConnect.receive_message()
                if sender not in self.inbox:
                    self.inbox[sender] = []
                self.inbox[sender].append(msg)

                if self.selectedChat == sender:
                    await self.display()
            except Exception as e:
                self.log(f"[!] Error receiving message: {e}")
                await asyncio.sleep(0.1)

    async def main(self):
        await self.clientConnect.connect()
        asyncio.create_task(self.receive_messages())

        self.selectedChat = (await self.async_input("Contact ID: ")).strip()

        await self.display()
        try:
            while True:
                msg = (await self.async_input("> ")).strip()
                if msg.lower() in ("quit", "exit"):
                    break
                if msg:
                    await self.clientConnect.send_message_to(self.selectedChat, msg)
                    if self.selectedChat not in self.inbox:
                        self.inbox[self.selectedChat] = []
                    self.inbox[self.selectedChat].append(f"> {msg}")
                    await self.display()
        except KeyboardInterrupt:
            self.log("[*] Keyboard interrupt received, closing client")
        finally:
            await self.clientConnect.close()
            self.log("[*] Client chiuso")


if __name__ == "__main__":
    Client()
