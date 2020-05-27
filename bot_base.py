import asyncio
import logging
import time
from cooldown import CooldownHelper


class BotBase:
    def __init__(self, bot):
        self.bot = bot
        self.auto_queue = True
        self.already_queued = False
        self.exclusive_run = False
        self.run_completed = True
        self.requeue_pending = None

    async def _queue_run(self, time):
        if time > 0:
            await asyncio.sleep(time)
        self.already_queued = False
        self.run_completed = False
        if self.exclusive_run:
            async with self.bot.exclusive_lock:
                await self.run()
        else:
            await self.run()
        self.run_completed = True
        if self.requeue_pending is not None:
            self.already_queued = False
            self.queue_run(self.requeue_pending)

    def queue_run(self, time):
        if self.already_queued:
            raise Exception("You already queued a re-run, don't do it again!")
        self.already_queued = True
        if not self.run_completed:
            self.requeue_pending = time
            return
        self.run_completed = False
        self.requeue_pending = None
        asyncio.create_task(self._queue_run(time))

    async def run(self):
        pass

    async def on_self_message(self, message):
        pass

    async def on_bot_message(self, message):
        pass

    async def on_bot_message_edit(self, message):
        pass


class SimpleBot(BotBase):
    def __init__(self, bot, name, cooldown_txt):
        super().__init__(bot)
        self.name = name
        self.log = logging.getLogger("bot." + name)
        self.cooldown = CooldownHelper(bot.config["cooldown"][name])
        self.cooldown_txt = cooldown_txt
        self.execution_timeout = time.time()
        self.exclusive_run = True

    async def run(self):
        self.log.info("Executing command")

        self.cooldown.on_send()
        self.reset_timeout()
        await self.send_command()
        next_try_in = self.bot.config["retry_on_timeout_s"]
        while True:
            remaining = self.execution_timeout - time.time()
            if remaining < 0.05:
                self.log.info("Timed out waiting for response")
                self.on_timeout()
                break
            try:
                await asyncio.wait_for(self.cooldown.wait(), remaining)
                next_try_in = self.cooldown.get_next_try_in()
                self.log.info("Finished successfully")
                break
            except asyncio.TimeoutError:
                pass
        self.log.info(f"Rescheduled in {next_try_in}s")
        self.queue_run(next_try_in)

    def on_timeout(self):
        pass

    def reset_timeout(self):
        self.execution_timeout = time.time() + self.bot.config["max_reply_s"]

    async def send_command(self):
        pass


class ActivationHelper:
    def __init__(self, bot):
        self.bot = bot
        self.active_on_channel = None
        self.active_time = None

    def reset_activation_timeout(self):
        if self.active_time is not None:
            self.active_time = time.time()

    def is_active(self, channel_id):
        if self.active_on_channel == channel_id:
            if time.time() > self.active_time + self.bot.config["max_reply_s"]:
                self.active_on_channel = None
                self.active_time = None
                return False
            return True
        return False

    def on_activated(self, channel_id):
        self.active_on_channel = channel_id
        self.active_time = time.time()

    def on_processed(self):
        self.active_on_channel = None
        self.active_time = None


class ActivatableSimpleBot(SimpleBot):
    def __init__(self, bot, name, cooldown_txt):
        super().__init__(bot, name, cooldown_txt)
        self.activation = ActivationHelper(bot)

    def reset_timeout(self):
        super().reset_timeout()
        self.activation.reset_activation_timeout()

    async def on_bot_message(self, message):
        if self.activation.is_active(message.channel.id):
            if self.cooldown.process_bot_message(message, self.cooldown_txt):
                self.activation.on_processed()
                return
            if await self.process_bot_message(message):
                self.activation.on_processed()
                self.cooldown.on_executed()

    async def on_self_message(self, message):
        if self.is_activation_command(message):
            self.activation.on_activated(message.channel.id)

    async def process_bot_message(self, message):
        pass

    def is_activation_command(self, message):
        return False


class ManualActivatableBot(BotBase):
    def __init__(self, bot, name, cooldown_txt):
        super().__init__(bot)
        self.name = name
        self.log = logging.getLogger("bot." + name)
        self.activation = ActivationHelper(bot)
        self.cooldown = CooldownHelper(bot.config["cooldown"][name])
        self.cooldown_txt = cooldown_txt

    async def on_bot_message(self, message):
        if self.activation.is_active(message.channel.id):
            if self.cooldown.process_bot_message(message, self.cooldown_txt):
                self.activation.on_processed()
                return
            if await self.process_bot_message(message):
                self.activation.on_processed()
                self.cooldown.on_executed()

    async def on_self_message(self, message):
        if self.is_activation_command(message):
            self.activation.on_activated(message.channel.id)

    async def process_bot_message(self, message):
        pass

    def is_activation_command(self, message):
        return False
