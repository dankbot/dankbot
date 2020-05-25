import discord
import logging
from asyncio import Lock, Event
from typer import MessageTyper
from inventory import InventoryTracker


class TheBot(discord.Client):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.log = logging.getLogger("bot")
        self.bots = []
        self.owner_id = config["owner_id"]
        self.notify_id = config["notify_id"]
        self.exclusive_lock = Lock()
        self.typer = MessageTyper(config["type_url"])
        self.inventory = InventoryTracker()
        self.notify_channel = None
        self.notify_channel_event = Event()
        self.typer.start()
        self.started_bots = False

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
        await self.notify_channel.send(f"<@!{self.notify_id}> {msg}")

    async def on_ready(self):
        self.log.info(f"Logged on as {self.user}")

        self.notify_channel = self.get_channel(self.config["notify_channel_id"])
        self.notify_channel_event.set()

        if not self.started_bots:
            self.started_bots = True
            for b in self.bots:
                b.queue_run(0)

    async def on_message(self, message):
        if message.channel.id == self.config["type_channel_id"]:
            self.log.info(f"Message from {message.author}: {message.content}")
            for e in message.embeds:
                self.log.info(f"Embed {e.title}: {e.description}")
        if message.author.id == self.owner_id:
            for b in self.bots:
                await b.on_self_message(message)
        if message.author.id == self.config["bot_id"]:
            for b in self.bots:
                await b.on_bot_message(message)

        if message.content.startswith("say "):
            await message.channel.send(message.content[4:])

        if message.content.startswith("plz "):
            args = message.content[4:].split(" ")
            if args[0] == "inv":
                e = discord.Embed(title='Grinded stuff')
                e.add_field(name="Coins", value=str(self.inventory.total_coins))
                inv = "; ".join(f"{k}: {v}" for k, v in self.inventory.items.items())
                if inv != "":
                    e.add_field(name="Inventory", value=inv)
                await message.channel.send("", embed=e)
            if args[0] == "stat" or args[0] == "stats":
                e = discord.Embed(title='The Stats')
                e.add_field(name="Coins", value="; ".join(f"{k}: {v}" for k, v in self.inventory.coins_stats.items()))
                await message.channel.send("", embed=e)

    async def on_message_edit(self, before, after):
        if after.author.id == self.config["bot_id"]:
            for b in self.bots:
                await b.on_bot_message_edit(after)

