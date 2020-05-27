from bot_base import BotBase, ActivationHelper
from bot_util import *
from cooldown import CooldownHelper
from inventory import InventoryTrackerListener
import logging
import asyncio
import random
import re


class AutoDepBot(BotBase, InventoryTrackerListener):
    P_REPLY_OK = re.compile("^([0-9,]+) coins deposited\\." + P_EOL)
    P_REPLY_BAD_VALUE = re.compile("^Your argument should be either a number and no more than what you have in your wallet \\(([0-9,]+)\\), or `max`" + P_EOL)
    COOLDOWN_TXT = "You'll be able to use this command again in "

    def __init__(self, bot):
        super().__init__(bot)
        self.log = logging.getLogger("bot.autodep")
        self.cooldown = CooldownHelper(bot.config["cooldown"]["dep"])
        self.activation = ActivationHelper(bot)
        self.exclusive_run = True
        self.threshold_min = self.bot.config["autodep_threshold"][0]
        self.threshold_max = self.bot.config["autodep_threshold"][1]
        self.result_min = self.bot.config["autodep_result"][0]
        self.result_max = self.bot.config["autodep_result"][1]
        self.regenerate_threshold()
        self.has_requested_dep = False
        self.bot.inventory.listeners.append(self)

    async def do_dep(self):
        use_cooldown = False
        while True:
            bring_to = random.randint(self.result_min, self.result_max)
            dep_cnt = self.bot.inventory.total_coins - bring_to
            if dep_cnt <= 0:
                break
            if use_cooldown:
                await asyncio.sleep(self.cooldown.get_next_try_in())
            self.cooldown.on_send()
            self.bot.typer.send_message(self.bot.get_prefixed_cmd(f"dep {dep_cnt}"))
            await self.cooldown.wait()
            use_cooldown = True
        self.has_requested_dep = False

    def request_dep(self):
        if self.has_requested_dep:
            return
        self.has_requested_dep = True
        asyncio.create_task(self.do_dep())

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd("dep "))

    def regenerate_threshold(self):
        self.threshold = random.randint(self.threshold_min, self.threshold_max)

    async def process_bot_message(self, message):
        r = AutoDepBot.P_REPLY_BAD_VALUE.match(message.content)
        if r:
            self.bot.inventory.total_coins = parse_bot_int(r.group(1))
            return True

        r = AutoDepBot.P_REPLY_OK.match(message.content)
        if r:
            self.bot.inventory.total_coins -= parse_bot_int(r.group(1))
            return True

        return False

    async def on_self_message(self, message):
        if self.is_activation_command(message):
            self.activation.on_activated(message.channel.id)

    async def on_bot_message(self, message):
        if self.activation.is_active(message.channel.id):
            if self.cooldown.process_bot_message(message, AutoDepBot.COOLDOWN_TXT):
                self.activation.on_processed()
                return
            if await self.process_bot_message(message):
                self.activation.on_processed()
                self.cooldown.on_executed()

    def on_coins_added(self, coins, source):
        if self.bot.inventory.total_coins >= self.threshold:
            self.regenerate_threshold()
            self.request_dep()

