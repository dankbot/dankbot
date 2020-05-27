import discord
import logging
from asyncio import Lock, Event

from bot_transfer import TransferBot
from bot_util import *
from bot_autodep import AutoDepBot
from bot_blackjack import BlackjackBot
from bot_invfetch import InvFetchBot
from typer import MessageTyper
from inventory import InventoryTracker
from bot_gamble import GambleBot


class TheBot(discord.Client):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.log = logging.getLogger("bot")
        self.bots = []
        self.owner_id = config["owner_id"]
        self.notify_id = config["notify_id"]
        self.exclusive_lock = Lock()
        self.typer = MessageTyper(config["profile_id"], config["type_url"])
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
                if b.auto_queue:
                    b.queue_run(0)

    async def on_message(self, message):
        if message.channel.id == self.config["type_channel_id"]:
            self.log.info(f"Message from {message.author}: {message.content}")
            for e in message.embeds:
                self.log.info(f"Embed {e.title}: {e.description}")
        if message.author.id == self.owner_id:
            message.content = filter_out_hint(message.content)
            for b in self.bots:
                await b.on_self_message(message)
        if message.author.id == self.config["bot_id"]:
            for b in self.bots:
                await b.on_bot_message(message)

        if message.content.startswith("plz ") and (message.author.id == self.notify_id or message.author.id == self.owner_id):
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
                str = f"u have {self.inventory.total_coins} in wallet, at least i think so.. (but i grinded {self.inventory.total_grinded})"
                autodep_bot = next((b for b in self.bots if isinstance(b, AutoDepBot)), None)
                if autodep_bot is not None:
                    str += f"; will dep at {autodep_bot.threshold}"
                await message.channel.send(str)
            if args[0] == "grind":
                e = discord.Embed(title='Grinded stuff')
                e.add_field(name="Coins", value=str(self.inventory.total_grinded))
                inv = "; ".join(f"{k}: {v}" for k, v in self.inventory.items.items())
                if inv != "":
                    e.add_field(name="Inventory", value=inv)
                await message.channel.send("", embed=e)
            if args[0] == "stat" or args[0] == "stats":
                e = discord.Embed(title='The Stats')
                e.add_field(name="Coins", value="; ".join(f"{k}: {v}" for k, v in self.inventory.coins_stats.items()))
                await message.channel.send("", embed=e)
            if args[0] == "gamble":
                gamble_bot = next((b for b in self.bots if isinstance(b, GambleBot)), None)
                if gamble_bot is None:
                    return
                e = discord.Embed(title='Gamble Stats')
                e.add_field(name="Won", value=f"{gamble_bot.won} games, {gamble_bot.won_money} coins")
                e.add_field(name="Lost", value=f"{gamble_bot.lost} games, {gamble_bot.lost_money} coins")
                e.add_field(name="Drew", value=f"{gamble_bot.draw} games, {gamble_bot.draw_lost_money} coins")
                await message.channel.send("", embed=e)
            if args[0] == "bj" or args[0] == "blackjack":
                blackjack_bot = next((b for b in self.bots if isinstance(b, BlackjackBot)), None)
                if blackjack_bot is None:
                    return
                e = discord.Embed(title='Blackjack Stats')
                e.add_field(name="Won", value=str(blackjack_bot.total_won))
                e.add_field(name="Lost", value=str(blackjack_bot.total_lost))
                e.add_field(name="Outcomes", value="; ".join(f"{k}: {v}" for k, v in blackjack_bot.outcomes.items()))
                await message.channel.send("", embed=e)
            if args[0] == "invfetch":
                invfetch_bot = next((b for b in self.bots if isinstance(b, InvFetchBot)), None)
                if invfetch_bot is None:
                    await message.channel.send("you disabled that bot, idiot")
                    return
                await message.channel.send("k give me a second")
                invfetch_bot.result_event.clear()
                invfetch_bot.queue_run(0)
                await invfetch_bot.result_event.wait()
                if invfetch_bot.inventory is not None:
                    await message.channel.send("; ".join(f"{k}: {v}" for [k, v] in invfetch_bot.inventory))
                else:
                    await message.channel.send("couldn't fetch inventory, probably memer memed on us")
            if args[0] == "transfer" and len(args) >= 2:
                transfer_bot = next((b for b in self.bots if isinstance(b, TransferBot)), None)
                if transfer_bot is None:
                    await message.channel.send("you disabled that bot, idiot")
                    return
                who = get_mention_user_id(args[1])
                list = parse_item_list(args[2:])
                await message.channel.send("list of items to transfer: " + "; ".join(f"{k}: {v}" for [k, v] in list))
                msg = await message.channel.send("i am just preparing for this...")

                for i, (what, cnt) in enumerate(list):
                    await msg.edit(content=f"`({i+1}/{len(list)})  GIVE {what} {cnt}`")
                    if not await transfer_bot.add(what, cnt, f"<@{who}>"):
                        await message.channel.send(f"failed to give {what} {cnt}")
                await msg.edit(content=f"done i think?")


    async def on_message_edit(self, before, after):
        if after.channel.id == self.config["type_channel_id"]:
            self.log.info(f"Edited message from {after.author}: {after.content}")
            for e in after.embeds:
                self.log.info(f"Embed {e.title}: {e.description}")
        if after.author.id == self.config["bot_id"]:
            for b in self.bots:
                await b.on_bot_message_edit(after)

