from bot_base import BotBase
from bot_util import *
import re
import time


class EventBot(BotBase):
    P_REPLY_NORMAL = re.compile(f"^{P_SHOP_ICON} \\*\\*`[A-Z ]+ EVENT TIME WOO!`\\*\\*\n")
    P_TYPE_NORMAL = re.compile(f"^Type `(.*)`" + P_EOL)
    P_TYPE_BOSS = re.compile(f"^Attack the boss by typing `(.*)` into chat!" + P_EOL)

    def __init__(self, bot):
        super().__init__(bot)
        self.invalidated = False
        self.event_started_time = None

    async def on_self_message(self, message):
        self.invalidated = True

    async def on_bot_message(self, message):
        if EventBot.P_REPLY_NORMAL.match(message.content):
            self.event_started_time = time.time()

        if self.event_started_time is not None:
            if time.time() - self.event_started_time > 3:  # expire the event if follow up not within 3s
                self.event_started_time = None
                return

            r = EventBot.P_TYPE_NORMAL.match(message.content)
            if r:
                self.event_started_time = None
                text = filter_ascii(r.group(1))
                await self.bot.send_notify("event in " + message.channel.mention + ": `" + text + "`")

            r = EventBot.P_TYPE_BOSS.match(message.content)
            if r:
                self.event_started_time = None
                text = filter_ascii(r.group(1))
                await self.bot.send_notify("boss event in " + message.channel.mention + ": `" + text + "`")
