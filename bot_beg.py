from bot_base import SimpleBot
from bot_util import *
import re


class BegBot(SimpleBot):
    P_REPLY_NORMAL = re.compile(f"^\\*\\*.*?\\*\\* has donated ([0-9,]+) coins to ({P_MENTION})!$")
    P_REPLY_ITEM = re.compile(f"^\\*\\*.*?\\*\\* has donated ([0-9,]+) coins to ({P_MENTION}), and a {P_SHOP_ICON} \\*\\*({P_SHOP_NAME})\\*\\*(?: WOW LUCKY)?$")
    COOLDOWN_TXT = "Stop begging so much, it makes you look like a little baby\\.\nYou can have more coins in "

    def __init__(self, bot):
        super().__init__(bot, "beg", BegBot.COOLDOWN_TXT)

    async def send_command(self):
        self.bot.typer.send_message(self.bot.get_prefixed_cmd("beg"))

    async def on_bot_message(self, message):
        self.cooldown.process_bot_message(message, self.cooldown_txt)

        r = BegBot.P_REPLY_NORMAL.match(message.content)
        if r and get_mention_user_id(r.group(2)) == self.bot.owner_id:
            self.bot.inventory.add_coins(int(r.group(1)), "beg")
            self.cooldown.on_executed()

        r = BegBot.P_REPLY_ITEM.match(message.content)
        if r and get_mention_user_id(r.group(2)) == self.bot.owner_id:
            self.bot.inventory.add_coins(int(r.group(1)), "beg")
            self.bot.inventory.add_item(r.group(3), 1, "beg")
            self.cooldown.on_executed()
