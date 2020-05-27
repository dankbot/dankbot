from bot_base import ActivatableSimpleBot
from bot_util import *
import re
import asyncio
import time
from asyncio import Lock


class TransferBot(ActivatableSimpleBot):
    P_FOOTER = re.compile("^Owned Items ─ Page ([0-9]+) of ([0-9]+)$")
    P_LIMIT = re.compile("^Slow down cowpoke, this person can't have more than [0-9,]+ of that. They already have [0-9,]+" + P_EOL)
    P_SUCCESS = re.compile(f"^You gave .+ \*\*([0-9]+)\*\* {P_SHOP_NAME}, now you have [0-9,]+ and they've got [0-9,]+" + P_EOL)
    P_ITEM = re.compile(f"^{P_SHOP_ICON} ?\\*\\*({P_SHOP_NAME})\\*\\* ─ ([0-9,]+)$", re.M)

    def __init__(self, bot):
        super().__init__(bot, "gift", None)
        self.auto_queue = False
        self.exclusive_run = True
        self.current_lock = Lock()
        self.current_item = 0
        self.current_count = 0
        self.current_target = 0
        self.current_event = asyncio.Event()
        self.current_result = False
        self.last_execute_time = 0

    async def add(self, what, count, to_who):
        async with self.current_lock:
            self.current_item = what
            self.current_count = count
            self.current_target = to_who
            self.current_event.clear()
            self.current_result = False

            if not self.already_queued and self.run_completed:
                self.queue_run(max(self.last_execute_time + self.cooldown.base - time.time() + 0.1, 0))
            await self.current_event.wait()
            return self.current_result

    async def run(self):
        await super().run()
        self.last_execute_time = time.time()

    async def send_command(self):
        if self.current_item is None:
            self.cooldown.on_executed()
            return
        self.bot.typer.send_message(self.bot.get_prefixed_cmd(f"gift {self.current_count} {self.current_item} {self.current_target}"))

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd(f"gift "))

    def should_reschedule(self):
        return self.current_item is not None

    async def process_bot_message(self, message):
        if self.current_item is None:
            return

        if TransferBot.P_LIMIT.match(message.content):
            await self.bot.send_notify(f"houston we have a problem, we ran into The Limit, check out https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}")
            self.current_item = None
            self.current_event.set()
            return True

        r = TransferBot.P_SUCCESS.match(message.content)
        if r and parse_bot_int(r.group(1)) == self.current_count:
            self.current_result = True
            self.current_item = None
            self.current_event.set()
            return True

        return

