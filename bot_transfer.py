from bot_base import SimpleTaskBot
from bot_util import *
import re


class TransferBot(SimpleTaskBot):
    P_LIMIT = re.compile("^Slow down cowpoke, this person can't have more than [0-9,]+ of that. They already have [0-9,]+" + P_EOL)
    P_SUCCESS = re.compile(f"^You gave .+ \*\*([0-9]+)\*\* {P_SHOP_NAME}, now you have [0-9,]+ and they've got [0-9,]+" + P_EOL)
    P_ITEM = re.compile(f"^{P_SHOP_ICON} ?\\*\\*({P_SHOP_NAME})\\*\\* ─ ([0-9,]+)$", re.M)

    def __init__(self, bot):
        super().__init__(bot, "gift", None)

    async def add(self, what, count, to_who):
        return await self.execute((what, count, to_who))

    def send_task_command(self, task):
        (task_what, task_count, task_who) = task
        self.bot.typer.send_message(self.bot.get_prefixed_cmd(f"gift {task_count} {task_what} {task_who}"))

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd(f"gift "))

    async def process_task_bot_message(self, task, message):
        if TransferBot.P_LIMIT.match(message.content):
            await self.bot.send_notify(f"houston we have a problem, we ran into The Limit, check out https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}")
            return False

        r = TransferBot.P_SUCCESS.match(message.content)
        (_, task_count, _) = task
        if r and parse_bot_int(r.group(1)) == task_count:
            return True

        return None

