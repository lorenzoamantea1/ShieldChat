import asyncio
import curses
import json
import os
from connection import ClientConnection
import textwrap

CONTACTS_FILE = "./storage/contacts.json"
RECEIVED_COLOR = 2
SENT_COLOR = 1
INFO_COLOR = 4

class ClientApp:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.client = ClientConnection()
        self.client_id = None
        self.contacts = {}
        self.inbox = {}
        self.selected_chat = None
        self.running = True
        self.scroll_offset = 0
        self.load_contacts()
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(SENT_COLOR, curses.COLOR_CYAN, -1)
        curses.init_pair(RECEIVED_COLOR, curses.COLOR_YELLOW, -1)
        curses.init_pair(INFO_COLOR, curses.COLOR_WHITE, -1)

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

    async def display_box(self, title, lines):
        self.stdscr.clear()
        h, w = self.stdscr.getmaxyx()
        box_height = h - 4
        box_width = w - 4
        start_y = 2
        start_x = 2

        self.stdscr.addstr(start_y, start_x, '┌' + '─' * (box_width - 2) + '┐', curses.color_pair(INFO_COLOR))
        for y in range(1, box_height - 1):
            self.stdscr.addstr(start_y + y, start_x, '│', curses.color_pair(INFO_COLOR))
            self.stdscr.addstr(start_y + y, start_x + 1, ' ' * (box_width - 2))
            self.stdscr.addstr(start_y + y, start_x + box_width - 1, '│', curses.color_pair(INFO_COLOR))
        self.stdscr.addstr(start_y + box_height - 1, start_x, '└' + '─' * (box_width - 2) + '┘', curses.color_pair(INFO_COLOR))

        display_title = f"{title} (ID: {self.client_id})" if self.client_id else title
        self.stdscr.addstr(start_y, start_x + 2, f" {display_title} ", curses.color_pair(INFO_COLOR) | curses.A_BOLD)

        visible_height = box_height - 3
        max_scroll = max(0, len(lines) - visible_height)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
        visible_lines = lines[self.scroll_offset:self.scroll_offset + visible_height]

        y_offset = start_y + 1
        for line, color in visible_lines:
            self.stdscr.addstr(y_offset, start_x + 2, line, curses.color_pair(color))
            y_offset += 1

        prompt_y = h - 2
        self.stdscr.addstr(prompt_y, start_x, "> ", curses.color_pair(INFO_COLOR))
        self.stdscr.move(prompt_y, start_x + 2)
        self.stdscr.refresh()


    async def display_contacts_box(self):
        lines = [(f"{idx}. {name} ({cid})", RECEIVED_COLOR) for idx, (cid, name) in enumerate(self.contacts.items(), start=1)]
        if len(self.contacts) < 20:
            lines.append(("- Add contact (add)", INFO_COLOR))
        await self.display_box("Contacts", lines)

    async def display_chat(self):
        chat_name = self.contacts.get(self.selected_chat, self.selected_chat)
        messages = self.inbox.get(self.selected_chat, [])
        await self.display_box(f"Chat with {chat_name}", messages)

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

                h, w = self.stdscr.getmaxyx()
                box_width = w - 4
                wrapped_lines = textwrap.wrap(f"{self.contacts.get(sender, sender)}: {msg}", width=box_width-4)
                for line in wrapped_lines:
                    self.inbox[sender].append((line, RECEIVED_COLOR))

                if self.selected_chat == sender:
                    await self.display()
            except:
                await asyncio.sleep(0.1)

    async def input_loop(self):
        curses.echo()
        while self.running:
            await self.display()
            h, w = self.stdscr.getmaxyx()
            prompt_y, prompt_x = h - 2, 2
            try:
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
        h, w = self.stdscr.getmaxyx()
        box_width = w - 4
        wrapped_lines = textwrap.wrap(f"> {msg}", width=box_width-4)
        for line in wrapped_lines:
            self.inbox[self.selected_chat].append((line, SENT_COLOR))
        await self.client.send_message_to(self.selected_chat, msg)
        self.scroll_offset = max(0, len(self.inbox[self.selected_chat]) - 1)

    async def prompt_input(self, prompt_text):
        h, w = self.stdscr.getmaxyx()
        self.stdscr.addstr(h-2, 2, prompt_text, curses.color_pair(INFO_COLOR))
        self.stdscr.clrtoeol()
        self.stdscr.refresh()
        input_bytes = await asyncio.to_thread(self.stdscr.getstr, h-2, 2 + len(prompt_text), w - 2 - len(prompt_text))
        return input_bytes.decode().strip()

    def select_contact(self, msg):
        for cid, name in self.contacts.items():
            if msg.lower() == name.lower() or msg == cid:
                return cid
        return None

    async def main(self):
        await self.client.connect()
        self.client_id = self.client.client_id
        asyncio.create_task(self.receive_messages())
        await self.input_loop()
        await self.client.close()

def start(stdscr):
    curses.curs_set(1)
    app = ClientApp(stdscr)
    asyncio.run(app.main())

if __name__ == "__main__":
    curses.wrapper(start)
