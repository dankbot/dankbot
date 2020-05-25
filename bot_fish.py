from bot_base import SimpleBot
from bot_util import *
import re


class FishBot(SimpleBot):
    P_FISH_DONE = re.compile(f"^You cast out your line and brought back ([0-9]*) ({P_SHOP_NAME}) {P_SHOP_ICON}!$")
    P_FISH_DONE2 = re.compile(f"^You cast out your line and brought back one ({P_SHOP_NAME}) {P_SHOP_ICON}, nice catch!$")
    P_FISH_FAIL = re.compile("^lol you suck, you found nothing$")
    P_FISH_RISK = re.compile("^ahhhhh the fish is too strong and your line is at risk to break! quick, type the phrase below in the next 10 seconds\nType `(.*)`$")
    P_NO_POLE = re.compile("^You don't have a fishing pole, you need to go buy one.$")
    COOLDOWN_TXT = "The fish seem weary of fishermen right now"

    def __init__(self, bot):
        super().__init__(bot, "fish", FishBot.COOLDOWN_TXT)

    async def send_command(self):
        self.bot.typer.send_message(self.bot.get_prefixed_cmd("fish"))

    def is_activation_command(self, message):
        return message.content == self.bot.get_prefixed_cmd("fish")

    async def process_bot_message(self, message):
        r = FishBot.P_FISH_DONE.match(message.content)
        if r:
            self.bot.inventory.add_item(r.group(2), int(r.group(1)), "fish")
            return True

        r = FishBot.P_FISH_DONE2.match(message.content)
        if r:
            self.bot.inventory.add_item(r.group(1), 1, "fish")
            return True

        r = FishBot.P_FISH_RISK.match(message.content)
        if r:
            self.bot.typer.send_message(filter_ascii(r.group(1)))
            return False

        if FishBot.P_FISH_FAIL.match(message.content):
            return True

        if FishBot.P_NO_POLE.match(message.content):
            await self.bot.send_notify(f"prob get a fishing pole dude")
            return True

        return False

