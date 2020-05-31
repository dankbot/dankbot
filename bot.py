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
from discord.ext.commands import CommandNotFound


class TheBot(Bot):
    def __init__(self, config):
        super().__init__(command_prefix="plz ", help_command=None)
        self.config = config
        self.log = logging.getLogger("bot")
        self.bots = []
        self.cmd_handlers = []
        self.user_id = None
        self.owner_id = config["owner_id"] if "owner_id" in config else None
        self.exclusive_lock = asyncio_rw_lock.FifoLock()
        self.typer = None
        self.inventory = InventoryTracker()
        self.notify_channel = None
        self.notify_channel_event = Event()
        self.started_bots = False
        self.typer = MessageTyper(self.config["profile_id"], None)

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
        if self.typer is not None:
            self.typer.stop()

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

            type_chan = self.get_channel(self.config["type_channel_id"])
            self.typer.url = f"https://discord.com/channels/{type_chan.guild.id}/{type_chan.id}"
            self.typer.start()
            self.user_id = await self.typer.get_user_id()

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
            self.typer.update_forced_cooldown(0.5)
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

    async def on_command_error(self, context, exception):
        if isinstance(exception, CommandNotFound):
            return
        logging.error("Command execution failed: " + str(context.command), exc_info=exception)


