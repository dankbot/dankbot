import discord
import logging
from asyncio import Event
import asyncio_rw_lock
from bot_cmd_main import MainCommandHandler
from bot_cmd_wrapper import WrapperCommandHandler
from bot_event import EventBot

from cmd_util import *
from typer import MessageTyper
from inventory import InventoryTracker

from bot_cmd_executor import BotCommandExecutor
from bot_auto import AutoBot

from discord.ext.commands import Bot


class TheBot(Bot):
    def __init__(self, config):
        super().__init__(command_prefix="plz ", help_command=None)
        self.config = config
        self.log = logging.getLogger("bot")
        self.bots = []
        self.cmd_handlers = []
        self.user_id = config["user_id"]
        self.owner_id = config["owner_id"]
        self.exclusive_lock = asyncio_rw_lock.FifoLock()
        self.typer = MessageTyper(config["profile_id"], config["type_url"])
        self.inventory = InventoryTracker()
        self.notify_channel = None
        self.notify_channel_event = Event()
        self.typer.start()
        self.started_bots = False

        self.cmd = BotCommandExecutor(self)
        self.auto = AutoBot(self)
        self.event_bot = EventBot(self)
        self.cmd_handler_main = MainCommandHandler(self)
        self.cmd_handler_wrapper = WrapperCommandHandler(self)

        self.add_cog(self.cmd_handler_main)
        self.add_cog(self.cmd_handler_wrapper)

    def add_bot(self, bot):
        self.bots.append(bot)

    def stop(self):
        self.typer.stop()
        pass

    def get_prefixed_cmd(self, cmd):
        return self.config["bot_prefix"] + " " + cmd

    def get_user_name(self):
        return self.get_user(self.user_id).name

    async def send_notify(self, msg):
        self.log.info(f"Sending notification: {msg}")
        await self.notify_channel_event.wait()
        await self.notify_channel.send(f"<@!{self.owner_id}> (<@{self.user_id}>) {msg}")

    async def on_ready(self):
        self.log.info(f"Logged on as {self.user}")

        self.notify_channel = self.get_channel(self.config["notify_channel_id"])
        self.notify_channel_event.set()

        if not self.started_bots:
            self.started_bots = True
            self.auto.start()

    async def on_message(self, message):
        if message.channel.id == self.config["type_channel_id"]:
            self.log.info(f"Message from {message.author}: {message.content}")
            for e in message.embeds:
                self.log.info(f"Embed {e.title}: {e.description}")
        if message.author.id == self.user_id:
            for b in self.cmd_handlers:
                b.on_user_message(message)
            await self.event_bot.on_user_message(message)
        if message.author.id == self.config["bot_id"]:
            message.content = filter_out_hint(message.content)
            for b in self.cmd_handlers:
                await b.on_bot_message(message)
            await self.event_bot.on_bot_message(message)

        await super().on_message(message)

    async def on_message_edit(self, before, after):
        if after.channel.id == self.config["type_channel_id"]:
            self.log.info(f"Edited message from {after.author}: {after.content}")
            for e in after.embeds:
                self.log.info(f"Embed {e.title}: {e.description}")
        if after.author.id == self.config["bot_id"]:
            await self.event_bot.on_bot_message_edit(after)


