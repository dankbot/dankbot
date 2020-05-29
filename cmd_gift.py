from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re


class GiftExecution(BaseExecution):
    T_USAGE = "awho tf are you giving coins to lmao, `gift <amount> <item> <@user or user id>` is how you use this"
    T_YOURSELF = "yeah you're a bit of an idiot, you can't share items with yourself"
    P_LIMIT = re.compile("^Slow down cowpoke, this person can't have more than [0-9,]+ of that. They already have [0-9,]+" + P_EOL)
    P_SUCCESS = re.compile(f"^You gave .+ \\*\\*([0-9,]+)\\*\\* {P_SHOP_NAME}, now you have [0-9,]+ and they've got [0-9,]+" + P_EOL)
    P_ITEM = re.compile(f"^{P_SHOP_ICON} ?\\*\\*({P_SHOP_NAME})\\*\\* ─ ([0-9,]+)$", re.M)

    def __init__(self, handler):
        super().__init__(handler)
        self.item = None
        self.item_count = 0
        self.target = None
        self.transferred = False

    def send_command(self, what, count, who):
        self.item = what
        self.item_count = count
        self.target = who
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd(f"gift {count} {what} {who}"))

    async def on_bot_message(self, message):
        if message.content in [GiftExecution.T_USAGE, GiftExecution.T_YOURSELF]:
            return True

        if GiftExecution.P_LIMIT.match(message.content):
            await self.bot.send_notify(f"houston we have a problem, we ran into The Limit, check out https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}")
            return True

        r = GiftExecution.P_SUCCESS.match(message.content)
        if r and (parse_bot_int(r.group(1)) == self.item_count or self.item is None):
            self.transferred = True
            return True

        return False

    def __str__(self):
        return f"GiftExecution: was_executed={self.was_executed} item={self.item} item_count={self.item_count} " \
               f"target={self.target} transferred={self.transferred}"


class GiftHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "gift")
        self.execution_factory = lambda: GiftExecution(self)

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd("gift "))
