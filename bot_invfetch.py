from discord import Embed

from bot_base import BotBase
from bot_util import *
from asyncio import Event
import asyncio
import re


class InvFetchBot(BotBase):
    P_FOOTER = re.compile("^Owned Items ─ Page ([0-9]+) of ([0-9]+)$")
    P_ITEM = re.compile(f"^{P_SHOP_ICON} ?\\*\\*({P_SHOP_NAME})\\*\\* ─ ([0-9,]+)$", re.M)

    def __init__(self, bot):
        super().__init__(bot)
        self.auto_queue = False
        self.exclusive_run = True
        self.inventory = None
        self.page = 0
        self.total_pages = 1
        self.page_recv_event = Event()
        self.result_event = Event()

    async def run(self):
        try:
            self.inventory = []
            self.page = 1
            self.total_pages = 1
            while self.page <= self.total_pages:
                self.page_recv_event.clear()
                self.bot.typer.send_message(self.bot.get_prefixed_cmd(f"inv {self.page}"))
                await asyncio.wait_for(self.page_recv_event.wait(), 10)
                self.page += 1
        except asyncio.TimeoutError:
            self.inventory = None
        self.result_event.set()

    async def on_bot_message(self, message):
        if message.content != "" or len(message.embeds) != 1:
            return

        e = message.embeds[0]
        our_user = self.bot.get_user(self.bot.owner_id)
        if e.author.name != our_user.name + "'s inventory":
            return
        if len(e.fields) != 1 or e.fields[0].name != "Owned Items":
            return

        if e.footer.text is not Embed.Empty:
            r = InvFetchBot.P_FOOTER.match(e.footer.text)
            if not r:
                return
            page = int(r.group(1))
            total_pages = int(r.group(2))
        else:
            page = 1
            total_pages = 1
        if page != self.page:
            return
        self.total_pages = total_pages

        print(e.fields[0].value)
        for r in InvFetchBot.P_ITEM.finditer(e.fields[0].value):
            self.inventory.append((r.group(1), parse_bot_int(r.group(2))))
        self.page_recv_event.set()

        return

