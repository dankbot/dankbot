import asyncio
import logging
import time
from cooldown import CooldownHelper


class BotBase:
    def __init__(self, bot):
        self.bot = bot
        self.already_queued = False
        self.exclusive_run = False

    async def _queue_run(self, time):
        await asyncio.sleep(time)
        self.already_queued = False
        if self.exclusive_run:
            async with self.bot.exclusive_lock:
                await self.run()
        else:
            await self.run()

    def queue_run(self, time):
        if self.already_queued:
            raise Exception("You already queued a re-run, don't do it again!")
        self.already_queued = True
        asyncio.create_task(self._queue_run(time))

    async def run(self):
        pass

    async def on_self_message(self, message):
        pass

    async def on_bot_message(self, message):
        pass


class SimpleBot(BotBase):
    def __init__(self, bot, name, cooldown_txt):
        super().__init__(bot)
        self.name = name
        self.logger = logging.getLogger("bot." + name)
        self.cooldown = CooldownHelper(bot.config["cooldown"][name])
        self.cooldown_txt = cooldown_txt
        self.active_on_channel = None
        self.active_time = None
        self.exclusive_run = True

    async def run(self):
        self.logger.info("Executing command")
        self.cooldown.on_send()
        await self.send_command()
        try:
            await asyncio.wait_for(self.cooldown.wait(), self.bot.config["max_reply_s"])
            next_try_in = self.cooldown.get_next_try_in()
        except asyncio.TimeoutError:
            self.logger.info("Timed out waiting for response")
            next_try_in = self.bot.config["retry_on_timeout_s"]
        self.logger.info(f"Rescheduled in {next_try_in}s")
        self.queue_run(next_try_in)

    async def on_self_message(self, message):
        if self.is_activation_command(message):
            self.active_on_channel = message.channel.id
            self.active_time = time.time()

    async def on_bot_message(self, message):
        if self.active_on_channel == message.channel.id:
            if time.time() > self.active_time + self.bot.config["max_reply_s"]:
                self.active_on_channel = None
                self.active_time = None
                return
            if self.cooldown.process_bot_message(message, self.cooldown_txt):
                self.active_on_channel = None
                self.active_time = None
                return
            if await self.process_bot_message(message):
                self.active_on_channel = None
                self.active_time = None
                self.cooldown.on_executed()

    async def send_command(self):
        pass

    def is_activation_command(self, message):
        return False

    async def process_bot_message(self, message):
        pass

