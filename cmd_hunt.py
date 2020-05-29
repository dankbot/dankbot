from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re


class HuntExecution(BaseExecution):
    P_HUNT_DONE = re.compile(f"^You went hunting in the woods and brought back a ({P_SHOP_NAME}) {P_SHOP_ICON}!" + P_EOL)
    P_HUNT_DRAGON = re.compile(f"^You went hunting, and came back with a fucking Dragon 🐲, what the hell\\?" + P_EOL)
    P_HUNT_FAIL = re.compile("^lmao you are terrible, you found nothing to hunt" + P_EOL)
    P_HUNT_FAIL2 = re.compile("^You went to shoot the dragon, and you weak little macaroni legs gave out and you fell\\. Missing the shot, the dragon ate you\\. LOL" + P_EOL)
    P_HUNT_RISK = re.compile("^Holy fucking shit god forbid you find something innocent like a duck, ITS A DRAGON! Type the phrase below in the next 10 seconds or you're toast!\nType `(.*)`" + P_EOL)
    P_NO_ITEM = re.compile("^You don't have a hunting rifle, you need to go buy one\\. You're not good enough to shoot animals with your bare hands\\." + P_EOL)
    COOLDOWN_TXT = "The forest seems a little empty right now, try again in "

    def __init__(self, handler):
        super().__init__(handler)
        self.cooldown_text = HuntExecution.COOLDOWN_TXT
        self.item = None
        self.risky_hunt = False
        self.no_rifle = False

    def send_command(self):
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd("hunt"))

    async def on_bot_message(self, message):
        r = HuntExecution.P_HUNT_DONE.match(message.content)
        if r:
            self.item = r.group(1)
            self.bot.inventory.add_item(self.item, 1, "hunt")
            return True

        r = HuntExecution.P_HUNT_DRAGON.match(message.content)
        if r:
            self.item = "Dragon"
            self.bot.inventory.add_item(self.item, 1, "hunt")
            return True

        r = HuntExecution.P_HUNT_RISK.match(message.content)
        if r:
            self.send_message_as_user(filter_ascii(r.group(1)))
            self.risky_hunt = True
            return False

        if HuntExecution.P_HUNT_FAIL.match(message.content) or HuntExecution.P_HUNT_FAIL2.match(message.content):
            return True

        if HuntExecution.P_NO_ITEM.match(message.content):
            await self.bot.send_notify(f"prob get a hunting rifle dude")
            self.no_rifle = True
            return True

        return False

    def __str__(self):
        return f"HuntExecution: was_executed={self.was_executed} item={self.item} risky_hunt={self.risky_hunt} " \
               f"no_rifle={self.no_rifle}"


class HuntHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "hunt")
        self.execution_factory = lambda: HuntExecution(self)
        self.requires_exclusivity = True

    def is_activation_command(self, message):
        return message.content == self.bot.get_prefixed_cmd("hunt")
