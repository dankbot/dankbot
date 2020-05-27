from bot_base import SimpleTaskBot
from bot_util import *
import re


class GiveBot(SimpleTaskBot):
    P_NOT_ENOUGH = re.compile("^You only have [0-9,]+ coins, you can't share that many" + P_EOL)
    P_SUCCESS = re.compile(f"^You gave .+ \*\*([0-9]+)\*\* coins after a [0-9,]% tax rate, now you have [0-9,]+ and they've got [0-9,]+" + P_EOL)
    P_ITEM = re.compile(f"^{P_SHOP_ICON} ?\\*\\*({P_SHOP_NAME})\\*\\* ─ ([0-9,]+)$", re.M)

    def __init__(self, bot):
        super().__init__(bot, "give", None)

    async def add(self, count, to_who):
        return await self.execute((count, to_who))

    def send_task_command(self, task):
        (task_count, task_who) = task
        self.bot.typer.send_message(self.bot.get_prefixed_cmd(f"give {task_count} {task_who}"))

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd(f"give "))

    async def process_task_bot_message(self, task, message):
        if GiveBot.P_NOT_ENOUGH.match(message.content):
            return False

        if GiveBot.P_SUCCESS.match(message.content):
            return True

        return None

