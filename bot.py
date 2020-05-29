import discord
import logging
from asyncio import Event
import asyncio_rw_lock
from bot_event import EventBot

from cmd_util import *
from typer import MessageTyper
from inventory import InventoryTracker

from bot_cmd import BotCommandExecutor
from bot_auto import AutoBot


class TheBot(discord.Client):
    def __init__(self, config):
        super().__init__()
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
            if args[0] == "dep":
                r = await self.cmd.deposit(int(args[1]))
                await message.channel.send(str(r))
            if args[0] == "withdraw":
                r = await self.cmd.withdraw(int(args[1]))
                await message.channel.send(str(r))
            if args[0] == "bal":
                r = await self.cmd.balance(args[1] if len(args) > 1 else None)
                await message.channel.send(str(r))
            if args[0] == "invfetch":
                r = await self.cmd.fetch_inventory()
                inv_str = "; ".join(f"{k}: {v}" for [k, v] in r)
                our_user = self.get_user(self.user_id)
                await message.channel.send(our_user.name + "'s inventory: " + inv_str)
            if args[0] == "transfer" and len(args) >= 2:
                who = get_mention_user_id(args[1])
                list = parse_item_list(args[2:])
                await message.channel.send("list of items to transfer: " + "; ".join(f"{k}: {v}" for [k, v] in list))
                msg = await message.channel.send("i am just preparing for this...")

                for i, (what, cnt) in enumerate(list):
                    await msg.edit(content=f"`({i+1}/{len(list)})  GIVE {what} {cnt}`")
                    if not (await self.cmd.gift(what, cnt, f"<@!{who}>")).transferred:
                        await message.channel.send(f"failed to give {what} {cnt}")
                await msg.edit(content=f"done i think?")
            if (args[0] == "slowgive" or args[0] == "sgive") and len(args) >= 2:
                who = get_mention_user_id(args[1])
                money = int(args[2])

                max_transfer = 10000
                transfer_cnt = (money + max_transfer - 1) // max_transfer
                msg = await message.channel.send(f"i am just preparing for this... ({transfer_cnt} transfers needed)")
                transfer_i = 0
                while money > 0:
                    transfer_i += 1
                    transfer_amount = min(money, max_transfer)
                    await msg.edit(content=f"`({transfer_i}/{transfer_cnt})  GIVE {transfer_amount} ({money} remaining)`")
                    if not (await self.cmd.give(transfer_amount, f"<@!{who}>")).transferred:
                        await message.channel.send(f"we failed somehow, sad and pitiful")
                        break
                    money -= transfer_amount
                await msg.edit(content=f"done i think?")

    async def on_message_edit(self, before, after):
        if after.channel.id == self.config["type_channel_id"]:
            self.log.info(f"Edited message from {after.author}: {after.content}")
            for e in after.embeds:
                self.log.info(f"Embed {e.title}: {e.description}")
        if after.author.id == self.config["bot_id"]:
            await self.event_bot.on_bot_message_edit(after)


