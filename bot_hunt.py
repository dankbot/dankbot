from bot_base import ActivatableSimpleBot
from bot_util import *
import re


class HuntBot(ActivatableSimpleBot):
    P_HUNT_DONE = re.compile(f"^You went hunting in the woods and brought back a ({P_SHOP_NAME}) {P_SHOP_ICON}!$")
    P_HUNT_DRAGON = re.compile(f"^You went hunting, and came back with a fucking Dragon 🐲, what the hell\\?$")
    P_HUNT_FAIL = re.compile("^lmao you are terrible, you found nothing to hunt$")
    P_HUNT_FAIL2 = re.compile("^You went to shoot the dragon, and you weak little macaroni legs gave out and you fell\\. Missing the shot, the dragon ate you\\. LOL$")
    P_HUNT_RISK = re.compile("^Holy fucking shit god forbid you find something innocent like a duck, ITS A DRAGON! Type the phrase below in the next 10 seconds or you're toast!\nType `(.*)`$")
    P_NO_ITEM = re.compile("^You don't have a hunting rifle, you need to go buy one\\. You're not good enough to shoot animals with your bare hands\\.$")
    COOLDOWN_TXT = "The forest seems a little empty right now, try again in "

    def __init__(self, bot):
        super().__init__(bot, "hunt", HuntBot.COOLDOWN_TXT)

    async def send_command(self):
        self.bot.typer.send_message(self.bot.get_prefixed_cmd("hunt"))

    def is_activation_command(self, message):
        return message.content == self.bot.get_prefixed_cmd("hunt")

    async def process_bot_message(self, message):
        r = HuntBot.P_HUNT_DONE.match(message.content)
        if r:
            self.bot.inventory.add_item(r.group(1), 1, "hunt")
            return True

        if HuntBot.P_HUNT_DRAGON.match(message.content):
            self.bot.inventory.add_item("Dragon", 1, "hunt")
            return True

        r = HuntBot.P_HUNT_RISK.match(message.content)
        if r:
            self.bot.typer.send_message(filter_ascii(r.group(1)))
            self.reset_timeout()
            return False

        if HuntBot.P_HUNT_FAIL.match(message.content) or HuntBot.P_HUNT_FAIL2.match(message.content):
            return True

        if HuntBot.P_NO_ITEM.match(message.content):
            await self.bot.send_notify(f"prob get a hunting rifle dude")
            return True

        return False

