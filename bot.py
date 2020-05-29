import discord
import logging
from asyncio import Lock, Event

from cmd_util import *
from typer import MessageTyper
from inventory import InventoryTracker

from bot_cmd import BotCommandExecutor


class TheBot(discord.Client):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.log = logging.getLogger("bot")
        self.bots = []
        self.cmd_handlers = []
        self.user_id = config["user_id"]
        self.owner_id = config["owner_id"]
        self.exclusive_lock = Lock()
        self.typer = MessageTyper(config["profile_id"], config["type_url"])
        self.inventory = InventoryTracker()
        self.notify_channel = None
        self.notify_channel_event = Event()
        self.typer.start()
        self.started_bots = False

        self.cmd = BotCommandExecutor(self)

    def add_bot(self, bot):
        self.bots.append(bot)

    def stop(self):
        self.typer.stop()
        pass

    def get_prefixed_cmd(self, cmd):
        return self.config["bot_prefix"] + " " + cmd

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
            for b in self.bots:
                if b.auto_queue:
                    b.queue_run(0)

    async def on_message(self, message):
        if message.channel.id == self.config["type_channel_id"]:
            self.log.info(f"Message from {message.author}: {message.content}")
            for e in message.embeds:
                self.log.info(f"Embed {e.title}: {e.description}")
        if message.author.id == self.user_id:
            for b in self.cmd_handlers:
                b.on_user_message(message)
        if message.author.id == self.config["bot_id"]:
            message.content = filter_out_hint(message.content)
            for b in self.cmd_handlers:
                await b.on_bot_message(message)

        if message.content.startswith("plz ") and (message.author.id == self.user_id or message.author.id == self.owner_id):
            def parse_item_list(arr):
                items = []
                for s in " ".join(arr).split(";"):
                    s = s.strip()
                    if s == "":
                        continue
                    if s[0].isdigit():
                        cnt, _, what = s.partition(" ")
                    elif s[-1].isdigit():
                        what, _, cnt = s.rpartition(" ")
                        if what.endswith(":"):
                            what = what[:-1]
                    else:
                        continue
                    what = what.strip()
                    cnt = cnt.strip()
                    if what == "" or cnt == "":
                        continue
                    items.append((what, int(cnt)))
                return items

            args = message.content[4:].split(" ")
            if args[0] == "wallet":
                our_user = self.get_user(self.user_id)
                s = f"{our_user}, u have {self.inventory.total_coins} in wallet, at least i think so.. (but i grinded {self.inventory.total_grinded})"
                await message.channel.send(s)
            if args[0] == "grind":
                our_user = self.get_user(self.user_id)
                e = discord.Embed(title=our_user.name + '\'s grind stats')
                e.add_field(name="Coins", value=str(self.inventory.total_grinded))
                inv = "; ".join(f"{k}: {v}" for k, v in self.inventory.items.items())
                if inv != "":
                    e.add_field(name="Inventory", value=inv)
                await message.channel.send("", embed=e)
            if args[0] == "stat" or args[0] == "stats":
                our_user = self.get_user(self.user_id)
                e = discord.Embed(title=our_user.name + '\'s stats')
                e.add_field(name="Coins", value="; ".join(f"{k}: {v}" for k, v in self.inventory.coins_stats.items()))
                await message.channel.send("", embed=e)
            if args[0] == "beg":
                r = await self.cmd.beg()
                await message.channel.send(str(r))
            if args[0] == "fish":
                r = await self.cmd.fish()
                await message.channel.send(str(r))
            if args[0] == "hunt":
                r = await self.cmd.hunt()
                await message.channel.send(str(r))
            if args[0] == "pm":
                r = await self.cmd.post_meme()
                await message.channel.send(str(r))
            if args[0] == "search":
                r = await self.cmd.search_with_preferences()
                await message.channel.send(str(r))


    async def on_message_edit(self, before, after):
        if after.channel.id == self.config["type_channel_id"]:
            self.log.info(f"Edited message from {after.author}: {after.content}")
            for e in after.embeds:
                self.log.info(f"Embed {e.title}: {e.description}")
        if after.author.id == self.config["bot_id"]:
            for b in self.bots:
                await b.on_bot_message_edit(after)

