from discord import Embed

from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re


class ProfileExecution(BaseExecution):
    P_LEVEL = re.compile("^\\*\\*([0-9,]+)\\*\\*\n")
    P_COINS = re.compile("^\\*\\*([0-9,]+)\\*\\* in wallet\n\\*\\*([0-9,]+)\\*\\* in bank\n\\*\\*([0-9.]+)%\\*\\* multiplier$")
    P_ITEM = re.compile(f"^{P_SHOP_ICON} ?\\*\\*({P_SHOP_NAME})\\*\\* - [^-]+ - expires in (.*)$", re.M)

    def __init__(self, handler):
        super().__init__(handler)
        self.account = None
        self.account_name = None
        self.level = None
        self.experience = None
        self.wallet = None
        self.bank = None
        self.multiplier = None
        self.active_items = []

    def send_command(self, whose=None):
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd(f"profile {whose}" if whose is not None else "profile"))

    def on_user_message(self, message, is_activation):
        if is_activation:
            str = self.bot.get_prefixed_cmd("profile ")
            if message.content.startswith(str):
                self.account = message.content[len(str):]

    async def on_bot_message(self, message):
        if message.content != "" or len(message.embeds) != 1:
            return False

        e = message.embeds[0]
        if e.author.name == Embed.Empty or not e.author.name.endswith("'s profile"):
            return False

        fields = {}
        for f in e.fields:
            fields[f.name] = f.value
        self.account_name = e.author.name[:-len("'s profile")]
        r = ProfileExecution.P_LEVEL.match(fields["Level"])
        self.level = parse_bot_int(r.group(1))
        r = ProfileExecution.P_LEVEL.match(fields["Experience"])
        self.experience = parse_bot_int(r.group(1))
        r = ProfileExecution.P_COINS.match(fields["Coins"])
        self.wallet = parse_bot_int(r.group(1))
        self.bank = parse_bot_int(r.group(2))
        self.multiplier = float(r.group(3))

        print(fields["Active Items"])
        for r in ProfileExecution.P_ITEM.finditer(fields["Active Items"]):
            self.active_items.append((r.group(1), parse_bot_time(r.group(2))))

        if self.account_name == self.bot.get_user_name() and self.account is None:
            self.bot.inventory.set_total_coins(self.wallet)
        return True

    def __str__(self):
        return f"ProfileExecution: was_executed={self.was_executed} account={self.account} " \
               f"account_name={self.account_name} wallet={self.wallet} bank={self.bank} multiplier={self.multiplier} " \
               f"active_items={self.active_items}"


class ProfileHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "profile")
        self.execution_factory = lambda: ProfileExecution(self)

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd("profile ")) or \
               message.content == self.bot.get_prefixed_cmd("profile")
