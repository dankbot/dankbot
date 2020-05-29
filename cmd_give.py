from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re


class GiveExecution(BaseExecution):
    T_USAGE = "who r u giving coins to, dumb"
    T_YOURSELF = "yeah you're a bit of an idiot, you can't share coins to yourself"
    P_NOT_ENOUGH = re.compile("You only have [0-9+]+ coins, you can't share that many" + P_EOL)
    P_SUCCESS = re.compile(f"^You gave .+ \\*\\*([0-9,]+)\\*\\* coins after a [0-9,]% tax rate, now you have [0-9,]+ and they've got [0-9,]+" + P_EOL)
    P_ITEM = re.compile(f"^{P_SHOP_ICON} ?\\*\\*({P_SHOP_NAME})\\*\\* ─ ([0-9,]+)$", re.M)

    def __init__(self, handler):
        super().__init__(handler)
        self.money = 0
        self.money_post_tax = 0
        self.target = None
        self.transferred = False

    def send_command(self, count, who):
        self.money = count
        self.target = who
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd(f"give {count} {who}"))

    async def on_bot_message(self, message):
        if message.content in [GiveExecution.T_USAGE, GiveExecution.T_YOURSELF]:
            return True

        if GiveExecution.P_NOT_ENOUGH.match(message.content):
            return True

        r = GiveExecution.P_SUCCESS.match(message.content)
        if r:
            self.transferred = True
            self.money_post_tax = parse_bot_int(r.group(1))
            return True

        return False

    def __str__(self):
        return f"GiveExecution: was_executed={self.was_executed} money={self.money} target={self.target} " \
               f"transferred={self.transferred}"


class GiveHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "give")
        self.execution_factory = lambda: GiveExecution(self)

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd("give "))
