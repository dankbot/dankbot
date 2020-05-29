import asyncio
from cooldown import CooldownHelper
import time
import logging


class BaseExecutionHandler:
    def __init__(self, bot, name):
        self.bot = bot
        self.name = name
        self.log = logging.getLogger("bot.cmd." + name)
        self.execution = None
        self.execution_factory = None
        self.execution_lock = asyncio.Lock()
        self.exclusive_lock_taken = False
        self.has_pending_execution = False
        self.cooldown = CooldownHelper(bot.config["cooldown"][name] if name in bot.config["cooldown"] else 10)
        self.no_cooldown = False
        self.requires_exclusivity = False
        bot.cmd_handlers.append(self)

    async def new_execution(self, no_lock=False):
        if not no_lock:
            await self.execution_lock.acquire()
        self.has_pending_execution = True
        if not self.no_cooldown:
            await asyncio.sleep(self.cooldown.get_wait_time())
        self.has_pending_execution = False
        if self.execution is not None:  # sorry, we lost to something
            return self.new_execution(True)
        if self.requires_exclusivity:
            await self.bot.exclusive_lock.acquire_write()
        else:
            await self.bot.exclusive_lock.acquire_read()
        self.exclusive_lock_taken = True
        self.execution = self.execution_factory()
        asyncio.create_task(self.execution.handle_timeout())
        return self.execution

    def on_execution_completed(self):
        self.log.info(f"Execution completed: {str(self.execution)}")
        self.execution = None
        if self.execution_lock.locked():
            self.execution_lock.release()
        if self.exclusive_lock_taken:
            self.exclusive_lock_taken = False
            if self.requires_exclusivity:
                self.bot.exclusive_lock.release_write()
            else:
                self.bot.exclusive_lock.release_read()

    def on_user_message(self, message):
        if self.execution is None and self.is_activation_command(message):
            self.execution = self.execution_factory()
            asyncio.create_task(self.execution.handle_timeout())
        if self.execution is not None:
            self.execution.dispatch_user_message(message)

    async def on_bot_message(self, message):
        if self.execution is not None:
            await self.execution.dispatch_bot_message(message)

    def is_activation_command(self, message):
        return False


class BaseExecution:
    def __await__(self):
        if self.request_command is None:
            raise Exception("You can only await executions that have called send_activation_message_as_user")
        return self.completion_future.__await__()

    def __init__(self, handler):
        self.handler = handler
        self.bot = handler.bot
        self.cooldown_text = None
        self.set_cooldown_on_finish = True
        self.request_command = None
        self.active = False
        self.expiry = time.time()
        self.completion_future = asyncio.Future()

        self.was_executed = False

        self.bump_timeout()

    async def handle_timeout(self):
        while not self.completion_future.done():
            timeout = self.expiry - time.time()
            if timeout <= 0:
                self.handler.log.info("Execution timed out")
                self.on_completed()
                return
            try:
                self.handler.log.info(f"handle_timeout: {timeout}")
                await asyncio.wait([self.completion_future], timeout=timeout)
            except asyncio.TimeoutError:
                pass

    def bump_timeout(self):
        self.handler.log.info("Timeout bumped")
        self.expiry = max(time.time() + self.handler.bot.config["max_reply_s"], self.expiry)

    def send_message_as_user(self, text):
        self.bot.typer.send_message(text)
        self.bump_timeout()

    def send_activation_message_as_user(self, text):
        assert(self.handler.execution is self)
        self.handler.cooldown.override_cooldown()
        self.send_message_as_user(text)
        self.request_command = text

    def dispatch_user_message(self, message):
        is_activation = False
        if (message.content == self.request_command or self.request_command is None) and not self.active:
            self.active = True
            self.bump_timeout()
            is_activation = True
        if self.active:
            self.on_user_message(message, is_activation)

    def on_completed(self):
        assert(self.handler.execution is self)
        self.handler.log.info("Execution completed")
        self.active = False
        self.handler.on_execution_completed()
        self.completion_future.set_result(True)

    async def dispatch_bot_message(self, message):
        if self.active:
            c = CooldownHelper.extract_cooldown(message, self.cooldown_text)
            if c is not None and not self.handler.no_cooldown:
                self.handler.log.info(f"Cooldown: {c}")
                self.handler.cooldown.override_cooldown(c)
                self.on_completed()
            elif await self.on_bot_message(message):
                self.was_executed = True
                if self.set_cooldown_on_finish:
                    self.handler.cooldown.override_cooldown()
                self.on_completed()

    def on_user_message(self, message, is_activation):
        pass

    async def on_bot_message(self, message):
        return False
