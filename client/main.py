import asyncio
import curses
import json
import os
from connection import ClientConnection

CONTACTS_FILE = "contacts.json"

class ClientApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.client = ClientConnection()
        self.client_id = self.client.client_id
        self.contacts = {}
        self.inbox = {}
        self.selected_chat = None
        self.running = True
        self.scroll_offset = 0
        self.load_contacts()
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)  # own message
        curses.init_pair(2, 81, -1)                 # received azzurro chiaro
        curses.init_pair(3, 81, -1)                 # header azzurro chiaro
        curses.init_pair(4, 81, -1)                 # prompt azzurro chiaro
        curses.init_pair(5, 81, -1)                 # testo default azzurro chiaro

    def load_contacts(self):
        if os.path.exists(CONTACTS_FILE):
            try:
                with open(CONTACTS_FILE, "r") as f:
                    self.contacts = json.load(f)
                    for cid in self.contacts:
                        self.inbox[cid] = []
            except:
                self.contacts = {}

    def save_contacts(self):
        try:
            with open(CONTACTS_FILE, "w") as f:
                json.dump(self.contacts, f)
        except:
            pass

    async def display_contacts_box(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        box_height = h - 4
        box_width = w - 4
        start_y = 2
        start_x = 2

        self.stdscr.addstr(start_y, start_x, '┌' + '─' * (box_width - 2) + '┐', curses.color_pair(3))
        for y in range(1, box_height - 1):
            self.stdscr.addstr(start_y + y, start_x, '│', curses.color_pair(3))
            self.stdscr.addstr(start_y + y, start_x + 1, ' ' * (box_width - 2))
            self.stdscr.addstr(start_y + y, start_x + box_width - 1, '│', curses.color_pair(3))
        self.stdscr.addstr(start_y + box_height - 1, start_x, '└' + '─' * (box_width - 2) + '┘', curses.color_pair(3))

        self.stdscr.addstr(start_y, start_x + 2, " Contacts ", curses.color_pair(3) | curses.A_BOLD)
        visible_height = box_height - 3
        lines = list(self.contacts.items())
        max_scroll = max(0, len(lines) - visible_height)
        self.scroll_offset = min(self.scroll_offset, max_scroll)
        visible_contacts = lines[self.scroll_offset:self.scroll_offset + visible_height]
        for idx, (cid, name) in enumerate(visible_contacts, start=1):
            self.stdscr.addstr(start_y + idx, start_x + 2, f"{idx + self.scroll_offset}. {name} ({cid})", curses.color_pair(5))
        if len(visible_contacts) < visible_height:
            self.stdscr.addstr(start_y + len(visible_contacts) + 1, start_x + 2, "- Add contact (add)", curses.color_pair(4))
        prompt_y = start_y + box_height
        self.stdscr.addstr(prompt_y, start_x, "> ", curses.color_pair(4))
        self.stdscr.move(prompt_y, start_x + 2)
        self.stdscr.refresh()

    async def display_chat(self):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        box_height = h - 4
        box_width = w - 4
        start_y = 2
        start_x = 2

        self.stdscr.addstr(start_y, start_x, '┌' + '─' * (box_width - 2) + '┐', curses.color_pair(3))
        for y in range(1, box_height - 1):
            self.stdscr.addstr(start_y + y, start_x, '│', curses.color_pair(3))
            self.stdscr.addstr(start_y + y, start_x + 1, ' ' * (box_width - 2))
            self.stdscr.addstr(start_y + y, start_x + box_width - 1, '│', curses.color_pair(3))
        self.stdscr.addstr(start_y + box_height - 1, start_x, '└' + '─' * (box_width - 2) + '┘', curses.color_pair(3))

        chat_name = self.contacts.get(self.selected_chat, self.selected_chat)
        self.stdscr.addstr(start_y, start_x + 2, f" Chat with {chat_name} ", curses.color_pair(3) | curses.A_BOLD)
        visible_height = box_height - 3
        lines = self.inbox.get(self.selected_chat, [])
        max_scroll = max(0, len(lines) - visible_height)
        self.scroll_offset = min(self.scroll_offset, max_scroll)
        visible_messages = lines[self.scroll_offset:self.scroll_offset + visible_height]
        for idx, (msg, color) in enumerate(visible_messages, start=1):
            self.stdscr.addstr(start_y + idx, start_x + 2, msg[:box_width - 4], curses.color_pair(color))
        prompt_y = start_y + box_height
        self.stdscr.addstr(prompt_y, start_x, "> ", curses.color_pair(4))
        self.stdscr.move(prompt_y, start_x + 2)
        self.stdscr.refresh()

    async def display(self):
        if self.selected_chat is None:
            await self.display_contacts_box()
        else:
            await self.display_chat()

    async def receive_messages(self):
        while self.running:
            try:
                sender, msg = await self.client.receive_message()
                if sender not in self.inbox:
                    self.inbox[sender] = []
                if sender not in self.contacts:
                    self.contacts[sender] = sender
                    self.save_contacts()
                self.inbox[sender].append((f"{self.contacts.get(sender,sender)}: {msg}", 2))
                if self.selected_chat == sender:
                    await self.display()
            except:
                await asyncio.sleep(0.1)

    async def input_loop(self):
        curses.echo()
        h, w = self.stdscr.getmaxyx()
        while self.running:
            await self.display()
            try:
                prompt_y = 2 + h - 4
                prompt_x = 2
                msg_bytes = await asyncio.to_thread(self.stdscr.getstr, prompt_y, prompt_x + 2, w - prompt_x - 3)
                msg = msg_bytes.decode().strip()
            except:
                continue
            if not msg:
                continue
            if msg.lower() in ("quit", "exit"):
                self.running = False
                break
            if msg.lower() == "up":
                self.scroll_offset = max(0, self.scroll_offset - 1)
                continue
            if msg.lower() == "down":
                self.scroll_offset += 1
                continue
            if self.selected_chat is None:
                if msg.lower() == "add":
                    new_id = await self.prompt_input("ID > ")
                    new_name = await self.prompt_input("Name > ")
                    if new_id and new_name and new_id not in self.contacts:
                        self.contacts[new_id] = new_name
                        self.inbox[new_id] = []
                        self.save_contacts()
                    continue
                selected = self.select_contact(msg)
                if selected:
                    self.selected_chat = selected
                continue
            await self.send_chat(msg)

    async def send_chat(self, msg):
        self.inbox[self.selected_chat].append((f"> {msg}", 1))
        await self.client.send_message_to(self.selected_chat, msg)
        self.scroll_offset = max(0, len(self.inbox[self.selected_chat]) - 1)

    async def prompt_input(self, prompt_text):
        h, _ = self.stdscr.getmaxyx()
        self.stdscr.addstr(h-2, 2, prompt_text, curses.color_pair(4))
        self.stdscr.clrtoeol()
        self.stdscr.refresh()
        input_bytes = await asyncio.to_thread(self.stdscr.getstr, h-2, 2 + len(prompt_text), 50)
        return input_bytes.decode().strip()

    def select_contact(self, msg):
        for cid, name in self.contacts.items():
            if msg.lower() == name.lower() or msg == cid:
                return cid
        return None

    async def main(self):
        await self.client.connect()
        asyncio.create_task(self.receive_messages())
        await self.input_loop()
        await self.client.close()

def start(stdscr):
    curses.curs_set(1)
    app = ClientApp(stdscr)
    asyncio.run(app.main())

if __name__ == "__main__":
    curses.wrapper(start)
