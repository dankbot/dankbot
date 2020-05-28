from bot_base import ActivatableSimpleBot
from bot_util import *
import re


class BegBot(ActivatableSimpleBot):
    P_REPLY_NORMAL = re.compile(f"^\\*\\*.*?\\*\\* has donated ([0-9,]+) coins to ({P_MENTION})!" + P_EOL)
    P_REPLY_ITEM = re.compile(f"^\\*\\*.*?\\*\\* has donated ([0-9,]+) coins to ({P_MENTION}), and a {P_SHOP_ICON} \\*\\*({P_SHOP_NAME})\\*\\*(?: WOW LUCKY)?" + P_EOL)
    P_REPLY_NO_MONEY_GUESS = re.compile(f"^\\*\\*.*?\\*\\*: .*" + P_EOL)
    COOLDOWN_TXT = "Stop begging so much, it makes you look like a little baby.\nYou can have more coins in "

    def __init__(self, bot):
        super().__init__(bot, "beg", BegBot.COOLDOWN_TXT)

    async def send_command(self):
        self.bot.typer.send_message(self.bot.get_prefixed_cmd("beg"))

    def is_activation_command(self, message):
        return message.content == self.bot.get_prefixed_cmd("beg")

    async def process_bot_message(self, message):
        r = BegBot.P_REPLY_NORMAL.match(message.content)
        if r and get_mention_user_id(r.group(2)) == self.bot.user_id:
            self.bot.inventory.add_coins(parse_bot_int(r.group(1)), "beg")
            return True

        r = BegBot.P_REPLY_ITEM.match(message.content)
        if r and get_mention_user_id(r.group(2)) == self.bot.user_id:
            self.bot.inventory.add_coins(parse_bot_int(r.group(1)), "beg")
            self.bot.inventory.add_item(r.group(3), 1, "beg")
            return True

        if BegBot.P_REPLY_NO_MONEY_GUESS.match(message.content):
            return True

        return False

