from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re


class BegExecution(BaseExecution):
    P_REPLY_NORMAL = re.compile(f"^\\*\\*.*?\\*\\* has donated ([0-9,]+) coins to ({P_MENTION})!" + P_EOL)
    P_REPLY_ITEM = re.compile(f"^\\*\\*.*?\\*\\* has donated ([0-9,]+) coins to ({P_MENTION}), and a {P_SHOP_ICON} \\*\\*({P_SHOP_NAME})\\*\\*(?: WOW LUCKY)?" + P_EOL)
    P_REPLY_NO_MONEY_GUESS = re.compile(f"^\\*\\*.*?\\*\\*: .*" + P_EOL)
    COOLDOWN_TXT = "Stop begging so much, it makes you look like a little baby.\nYou can have more coins in "

    def __init__(self, handler):
        super().__init__(handler)
        self.cooldown_text = BegExecution.COOLDOWN_TXT
        self.money = 0
        self.item = None

    def send_command(self):
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd("beg"))

    async def on_bot_message(self, message):
        r = BegExecution.P_REPLY_NORMAL.match(message.content)
        if r and get_mention_user_id(r.group(2)) == self.bot.user_id:
            self.money = parse_bot_int(r.group(1))
            self.bot.inventory.add_coins(self.money, "beg")
            return True

        r = BegExecution.P_REPLY_ITEM.match(message.content)
        if r and get_mention_user_id(r.group(2)) == self.bot.user_id:
            self.money = parse_bot_int(r.group(1))
            self.item = r.group(3)
            self.bot.inventory.add_coins(self.money, "beg")
            self.bot.inventory.add_item(self.item, 1, "beg")
            return True

        if BegExecution.P_REPLY_NO_MONEY_GUESS.match(message.content):
            return True

        return False

    def __str__(self):
        return f"BegExecution: was_executed={self.was_executed} money={self.money} item={self.item}"


class BegHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "beg")
        self.execution_factory = lambda: BegExecution(self)

    def is_activation_command(self, message):
        return message.content == self.bot.get_prefixed_cmd("beg")
