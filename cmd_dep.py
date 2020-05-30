from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re


class DepositExecution(BaseExecution):
    T_USAGE = "what are you depositing, idiot"
    T_INVALID_NUMBER = "Needs to be a whole number greater than 0"
    P_NOT_ENOUGH = re.compile("^Your argument should be either a number and no more than what you have in your wallet \\(-?[0-9,]+\\), or `max`" + P_EOL)
    P_LIMIT = re.compile("^You can only hold \\*\\*[0-9,]+\\*\\* coins in your bank right now. To hold more, use currency commands and level up more." + P_EOL)
    P_SUCCESS = re.compile(f"^\\*\\*([0-9,]+)\\*\\* coins? deposited" + P_EOL)
    P_SUCCESS2 = re.compile(f"^([0-9,]+) coins? deposited." + P_EOL)

    def __init__(self, handler):
        super().__init__(handler)
        self.amount = 0
        self.success = False

    def send_command(self, amount):
        self.amount = amount
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd(f"dep {amount}"))

    async def on_bot_message(self, message):
        if message.content in [DepositExecution.T_USAGE, DepositExecution.T_INVALID_NUMBER]:
            return True

        if DepositExecution.P_NOT_ENOUGH.match(message.content):
            return True

        if DepositExecution.P_LIMIT.match(message.content):
            return True

        for s in [DepositExecution.P_SUCCESS, DepositExecution.P_SUCCESS2]:
            r = s.match(message.content)
            if r and self.amount == parse_bot_int(r.group(1)):
                self.bot.inventory.add_total_coins(-r.group(1))
                self.success = True
                return True

        return False

    def __str__(self):
        return f"DepositExecution: was_executed={self.was_executed} amount={self.amount} success={self.success}"


class DepositHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "dep")
        self.execution_factory = lambda: DepositExecution(self)

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd("dep "))
