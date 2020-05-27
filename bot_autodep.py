from bot_base import ActivatableSimpleBot, ActivationHelper
from bot_util import *
from inventory import InventoryTrackerListener
import random
import re


class AutoDepBot(ActivatableSimpleBot, InventoryTrackerListener):
    P_REPLY_OK = re.compile("^([0-9,]+) coins deposited\\." + P_EOL)
    P_REPLY_BAD_VALUE = re.compile("^Your argument should be either a number and no more than what you have in your wallet \\(([0-9,]+)\\), or `max`" + P_EOL)

    def __init__(self, bot):
        super().__init__(bot, "dep", None)
        self.activation = ActivationHelper(bot)
        self.exclusive_run = True
        self.auto_queue = False
        self.threshold_min = self.bot.config["autodep_threshold"][0]
        self.threshold_max = self.bot.config["autodep_threshold"][1]
        self.threshold = None
        self.regenerate_threshold()
        self.result_min = self.bot.config["autodep_result"][0]
        self.result_max = self.bot.config["autodep_result"][1]
        self.bot.inventory.listeners.append(self)

    def get_dep_amount(self):
        bring_to = random.randint(self.result_min, self.result_max)
        return self.bot.inventory.total_coins - bring_to

    async def send_command(self):
        dep_cnt = self.get_dep_amount()
        if dep_cnt <= 0:
            self.cooldown.on_executed()
            return
        self.bot.typer.send_message(self.bot.get_prefixed_cmd(f"dep {dep_cnt}"))

    def should_reschedule(self):
        return self.bot.inventory.total_coins >= self.threshold

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
            self.bot.inventory.total_coins = max(self.bot.inventory.total_coins - parse_bot_int(r.group(1)), 0)
            return True

        return False

    def on_coins_added(self, coins, source):
        if self.bot.inventory.total_coins >= self.threshold:
            self.regenerate_threshold()
            if not self.already_queued:
                self.queue_run(0)

