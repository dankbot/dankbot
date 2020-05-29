from discord import Embed

from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re


class InventoryExecution(BaseExecution):
    P_FOOTER = re.compile("^Owned Items ─ Page ([0-9]+) of ([0-9]+)$")
    P_ITEM = re.compile(f"^{P_SHOP_ICON} ?\\*\\*({P_SHOP_NAME})\\*\\* ─ ([0-9,]+)$", re.M)

    def __init__(self, handler):
        super().__init__(handler)
        self.page = 0
        self.total_pages = 0
        self.items = []

    def send_command(self, page):
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd(f"inv {page}"))

    def on_user_message(self, message, is_activation):
        if is_activation:
            str = self.bot.get_prefixed_cmd("inv ")
            if message.content.startswith(str):
                self.page = int(message.content[len(str):])

    async def on_bot_message(self, message):
        if message.content != "" or len(message.embeds) != 1:
            return False

        e = message.embeds[0]
        our_user = self.bot.get_user(self.bot.user_id)
        if e.author.name != our_user.name + "'s inventory":
            return False
        if len(e.fields) != 1 or e.fields[0].name != "Owned Items":
            return False

        if e.footer.text is not Embed.Empty:
            r = InventoryExecution.P_FOOTER.match(e.footer.text)
            if not r:
                return False
            page = int(r.group(1))
            total_pages = int(r.group(2))
        else:
            page = 1
            total_pages = 1
        if page != self.page:
            return
        self.total_pages = total_pages

        for r in InventoryExecution.P_ITEM.finditer(e.fields[0].value):
            self.items.append((r.group(1), parse_bot_int(r.group(2))))
        return True

    def __str__(self):
        return f"InventoryExecution: was_executed={self.was_executed} page={self.page} " \
               f"total_pages={self.total_pages} items={self.items}"


class InventoryHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "inv")
        self.no_cooldown = True
        self.execution_factory = lambda: InventoryExecution(self)

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd("inv "))
