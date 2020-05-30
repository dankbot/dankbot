from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re


class UseExecution(BaseExecution):
    T_USAGE = "That item doesn't even exist what are you doing"
    T_NOT_OWNED = "You don't own this item??"
    P_CHEESE_FAIL = re.compile("^<:chickycheese:583318568100429826> Uh oh.. your lactose intolerance is acting up\\. You feel extremely nauseous and you literally shit out `[0-9]+` experience points\\." + P_EOL)
    P_CHEESE_OK = re.compile(f"^<:chickycheese:583318568100429826> It's three o'clock in the morning\\. You're standing, barefoot, in front of the fridge\\." + P_EOL)

    def __init__(self, handler):
        super().__init__(handler)
        self.item = None
        self.used = False
        self.not_owned = False

    def send_command(self, what, count=None):
        count_str = f" {count}" if count is not None else ""
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd(f"use {what}{count_str}"))
        self.item = what
        if what == "cheese":
            self.send_message_as_user("y")

    async def on_bot_message(self, message):
        if message.content == UseExecution.T_USAGE:
            return True
        if message.content == UseExecution.T_NOT_OWNED:
            self.not_owned = True
            return True

        if self.item == "cheese":
            if UseExecution.P_CHEESE_OK.match(message.content) or UseExecution.P_CHEESE_FAIL.match(message.content):
                self.used = True
                return True

        return False

    def __str__(self):
        return f"UseExecution: was_executed={self.was_executed} item={self.item} used={self.used} " \
               f"not_owned={self.not_owned}"


class UseHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "use")
        self.execution_factory = lambda: UseExecution(self)

    def is_activation_command(self, message):
        return False  # don't
