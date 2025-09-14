import asyncio
import time
import curses
import json
import os
from connection import ClientConnection

CONTACTS_FILE = "contacts.json"

class UI:
    def __init__(self, stdscr, client_id):
        self.stdscr = stdscr
        self.client_id = client_id
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)

    def header(self, w):
        header_text = f" ShieldChat - Your ID: {self.client_id} "
        self.stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        if len(header_text) > w:
            header_text = header_text[:w-3] + "..."
        self.stdscr.addstr(0, 0, header_text.center(w, " "))
        self.stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)

    def log(self, msg):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(h-1, 0, f"[{time.strftime('%H:%M:%S')}] {msg}".ljust(w), curses.color_pair(3))
        self.stdscr.refresh()

class ClientApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.clientConnect = ClientConnection()
        self.client_id = self.clientConnect.client_id
        self.selectedChat = None
        self.inbox = {}
        self.running = True
        self.ui = UI(stdscr, self.client_id)
        self.load_contacts()
        self.scroll_offset = 0

    def load_contacts(self):
        if os.path.exists(CONTACTS_FILE):
            try:
                with open(CONTACTS_FILE, "r") as f:
                    self.contacts = json.load(f)
                    for cid in self.contacts.keys():
                        self.inbox[cid] = []
            except:
                self.contacts = {}
        else:
            self.contacts = {}

    def save_contacts(self):
        try:
            with open(CONTACTS_FILE, "w") as f:
                json.dump(self.contacts, f)
        except:
            pass

    async def display(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        self.ui.header(w)
        content_height = h - 3
        lines = []

        if self.selectedChat is None:
            lines.append("Contacts:")
            for idx, (cid, name) in enumerate(self.contacts.items(), start=1):
                text = f"{idx}. {name} ({cid})"
                if len(text) > w-2:
                    text = text[:w-5] + "..."
                lines.append(text)
            lines.append("- Add contact (add)")
        else:
            chat_name = self.contacts.get(self.selectedChat, self.selectedChat)
            lines.append(f"Chat with {chat_name}:")
            if self.selectedChat in self.inbox:
                for msg_text, color_id in self.inbox[self.selectedChat]:
                    if len(msg_text) > w-2:
                        msg_text = msg_text[:w-5] + "..."
                    lines.append((msg_text, color_id))

        max_scroll = max(0, len(lines) - content_height)
        self.scroll_offset = min(self.scroll_offset, max_scroll)
        visible_lines = lines[self.scroll_offset:self.scroll_offset+content_height]

        for i, line in enumerate(visible_lines, start=1):
            if isinstance(line, tuple):
                text, color_id = line
                self.stdscr.addstr(i, 1, text, curses.color_pair(color_id))
            else:
                self.stdscr.addstr(i, 1, line, curses.color_pair(5))

        input_row = h - 3
        input_col = 1
        prompt = "> " if self.selectedChat is None else ">"
        offset = len(prompt)
        self.stdscr.addstr(input_row, input_col, prompt, curses.color_pair(4))
        self.stdscr.move(input_row, input_col + offset)
        self.stdscr.refresh()

    async def receive_messages(self):
        while self.running:
            try:
                sender, msg = await self.clientConnect.receive_message()
                if sender not in self.inbox:
                    self.inbox[sender] = []
                    if sender not in self.contacts:
                        self.contacts[sender] = sender
                        self.save_contacts()
                self.inbox[sender].append((f"{self.contacts.get(sender,sender)}: {msg}", 2))
                if self.selectedChat == sender:
                    await self.display()
            except:
                await asyncio.sleep(0.1)

    async def input_loop(self):
        h, w = self.stdscr.getmaxyx()
        curses.echo()
        self.stdscr.keypad(True)
        while self.running:
            await self.display()
            try:
                input_row = h - 3
                input_col = 1
                offset = 2 if self.selectedChat is None else 1
                msg_bytes = await asyncio.to_thread(self.stdscr.getstr, input_row, input_col + offset, w-2)
                msg = msg_bytes.decode().strip()
            except:
                continue

            if msg.lower() in ("quit", "exit"):
                self.running = False
                break

            if msg == "":
                continue

            if msg.lower() in ("up", "down"):
                if msg.lower() == "up":
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                else:
                    self.scroll_offset += 1
                continue

            if self.selectedChat is None:
                if msg.lower() == "add":
                    new_id = await self.prompt_input("Enter new contact ID > ", 22)
                    new_name = await self.prompt_input("Enter contact name > ", 20)
                    if new_id and new_name and new_id not in self.contacts:
                        self.contacts[new_id] = new_name
                        self.inbox[new_id] = []
                        self.save_contacts()
                    continue
                selected = self.select_contact(msg)
                if selected:
                    self.selectedChat = selected
                continue

            await self.send_chat(msg)

    async def send_chat(self, msg):
        if self.selectedChat not in self.inbox:
            self.inbox[self.selectedChat] = []
        self.inbox[self.selectedChat].append((f"> {msg}", 1))
        await self.clientConnect.send_message_to(self.selectedChat, msg)
        self.scroll_offset = max(0, len(self.inbox[self.selectedChat]) + 1)

    async def prompt_input(self, prompt_text, col_start):
        h, _ = self.stdscr.getmaxyx()
        self.stdscr.addstr(h-3, 0, prompt_text)
        self.stdscr.clrtoeol()
        self.stdscr.refresh()
        input_bytes = await asyncio.to_thread(self.stdscr.getstr, h-3, col_start, 50)
        return input_bytes.decode().strip()

    def select_contact(self, msg):
        for cid, name in self.contacts.items():
            if msg.lower() == name.lower() or msg == cid:
                return cid
        return None

    async def main(self):
        await self.clientConnect.connect()
        asyncio.create_task(self.receive_messages())
        await self.input_loop()
        await self.clientConnect.close()
        self.ui.log("[*] Client closed")

def start(stdscr):
    curses.curs_set(1)
    client = ClientApp(stdscr)
    asyncio.run(client.main())

if __name__ == "__main__":
    curses.wrapper(start)
