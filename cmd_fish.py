from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re


class FishExecution(BaseExecution):
    P_FISH_DONE = re.compile(f"^You cast out your line and brought back ([0-9]*) ({P_SHOP_NAME}) {P_SHOP_ICON}!" + P_EOL)
    P_FISH_DONE2 = re.compile(f"^You cast out your line and brought back one ({P_SHOP_NAME}) {P_SHOP_ICON}, nice catch!" + P_EOL)
    P_FISH_FAIL = re.compile("^lol you suck, you found nothing" + P_EOL)
    P_FISH_FAIL2 = re.compile("^oh snap, your fishing pole fell in the water bc the force of the OP AF fish was too much for your weak little macaroni arms!" + P_EOL)
    P_FISH_RISK = re.compile("^ahhhhh the fish is too strong and your line is at risk to break! quick, type the phrase below in the next 10 seconds\nType `(.*)`" + P_EOL)
    P_NO_ITEM = re.compile("^You don't have a fishing pole, you need to go buy one\\." + P_EOL)
    COOLDOWN_TXT = "The fish seem weary of fishermen right now, try again in "

    def __init__(self, handler):
        super().__init__(handler)
        self.cooldown_text = FishExecution.COOLDOWN_TXT
        self.item = None
        self.item_count = 0
        self.risky_catch = False
        self.no_pole = False

    def send_command(self):
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd("fish"))

    async def on_bot_message(self, message):
        r = FishExecution.P_FISH_DONE.match(message.content)
        if r:
            self.item = r.group(2)
            self.item_count = parse_bot_int(r.group(1))
            self.bot.inventory.add_item(self.item, self.item_count, "fish")
            return True

        r = FishExecution.P_FISH_DONE2.match(message.content)
        if r:
            self.item = r.group(1)
            self.item_count = 1
            self.bot.inventory.add_item(self.item, self.item_count, "fish")
            return True

        r = FishExecution.P_FISH_RISK.match(message.content)
        if r:
            self.send_message_as_user(filter_ascii(r.group(1)))
            self.risky_catch = True
            return False

        if FishExecution.P_FISH_FAIL.match(message.content) or FishExecution.P_FISH_FAIL2.match(message.content):
            return True

        if FishExecution.P_NO_ITEM.match(message.content):
            await self.bot.send_notify(f"prob get a fishing pole dude")
            self.no_pole = True
            return True

        return False

    def __str__(self):
        return f"FishExecution: was_executed={self.was_executed} item={self.item} item_count={self.item_count} " \
               f"risky_catch={self.risky_catch} no_pole={self.no_pole}"


class FishHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "fish")
        self.execution_factory = lambda: FishExecution(self)
        self.requires_exclusivity = True

    def is_activation_command(self, message):
        return message.content == self.bot.get_prefixed_cmd("fish")
