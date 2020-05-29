from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re


class BalanceExecution(BaseExecution):
    P_CONTENT = re.compile("\\*\\*Wallet\\*\\*: ([0-9,]+)\n\\*\\*Bank\\*\\*: ([0-9,]+)")

    def __init__(self, handler):
        super().__init__(handler)
        self.account = None
        self.account_name = None
        self.wallet = 0
        self.bank = 0
        self.success = False

    def send_command(self, whose=None):
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd(f"bal {whose}" if whose is not None else "bal"))

    def on_user_message(self, message, is_activation):
        if is_activation:
            str = self.bot.get_prefixed_cmd("bal ")
            if message.content.startswith(str):
                self.account = message.content[len(str):]

    async def on_bot_message(self, message):
        if message.content != "" or len(message.embeds) != 1:
            return False

        e = message.embeds[0]
        if not e.title.endswith("'s balance"):
            return False
        r = BalanceExecution.P_CONTENT.match(e.description)
        if not r:
            return False

        self.account_name = e.title[:-len("'s balance")]
        self.wallet = parse_bot_int(r.group(1))
        self.bank = parse_bot_int(r.group(2))
        return True

    def __str__(self):
        return f"BalanceExecution: was_executed={self.was_executed} account={self.account} " \
               f"account_name={self.account_name} wallet={self.wallet} bank={self.bank}"


class BalanceHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "balance")
        self.execution_factory = lambda: BalanceExecution(self)

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd("bal ")) or \
               message.content == self.bot.get_prefixed_cmd("bal")
