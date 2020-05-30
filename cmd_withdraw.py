from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re


class WithdrawExecution(BaseExecution):
    T_USAGE = "what are you withdrawing, dummy"
    T_INVALID_NUMBER = "Needs to be a whole number greater than 0"
    P_NOT_ENOUGH = re.compile("^Your second argument should be a number and no more than what you have in your bank \\([0-9,]+\\)" + P_EOL)
    P_SUCCESS = re.compile(f"^\\*\\*([0-9,]+)\\*\\* coins? withdrawn" + P_EOL)
    P_SUCCESS2 = re.compile(f"^([0-9,]+) coins? withdrawn." + P_EOL)

    def __init__(self, handler):
        super().__init__(handler)
        self.amount = 0
        self.success = False

    def send_command(self, amount):
        self.amount = amount
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd(f"withdraw {amount}"))

    async def on_bot_message(self, message):
        if message.content in [WithdrawExecution.T_USAGE, WithdrawExecution.T_INVALID_NUMBER]:
            return True

        if WithdrawExecution.P_NOT_ENOUGH.match(message.content):
            return True

        for s in [WithdrawExecution.P_SUCCESS, WithdrawExecution.P_SUCCESS2]:
            r = s.match(message.content)
            if r and self.amount == parse_bot_int(r.group(1)):
                self.bot.inventory.add_total_coins(self.amount)
                self.success = True
                return True

        return False

    def __str__(self):
        return f"WithdrawExecution: was_executed={self.was_executed} amount={self.amount} success={self.success}"


class WithdrawHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "withdraw")
        self.execution_factory = lambda: WithdrawExecution(self)

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd("withdraw "))
