from bot_base import BotBase
from bot_util import *
import re
import time
import asyncio
import random


class EventBot(BotBase):
    P_REPLY_NORMAL = re.compile(f"^{P_SHOP_ICON} \\*\\*`[A-Z ]+ EVENT TIME WOO!`\\*\\*\n")
    P_TYPE_NORMAL = re.compile(f"^Type `(.*)`" + P_EOL)
    P_TYPE_BOSS = re.compile(f"^Attack the boss by typing `(.*)` into chat!" + P_EOL)

    def __init__(self, bot):
        super().__init__(bot)
        self.event_started_time = None
        self.spam_msg = None
        self.spam_msg_cnt = 0
        self.spam_task_running = False

    async def on_self_message(self, message):
        # invalidate any pending messages
        self.spam_msg = None
        self.spam_msg_cnt = 0

    async def on_bot_message(self, message):
        can_just_type = message.channel.id == self.bot.config["type_channel_id"]

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
                if can_just_type:
                    self.start_send_spam(text, 1)
                await self.bot.send_notify("event in " + message.channel.mention + ": `" + text + "`")

            r = EventBot.P_TYPE_BOSS.match(message.content)
            if r:
                self.event_started_time = None
                text = filter_ascii(r.group(1))
                if can_just_type:
                    self.start_send_spam(text, 10)
                await self.bot.send_notify("boss event in " + message.channel.mention + ": `" + text + "`")

    def start_send_spam(self, msg, cnt):
        self.spam_msg = msg
        self.spam_msg_cnt = cnt
        if not self.spam_task_running:
            self.spam_task_running = True
            asyncio.create_task(self.send_spam())

    async def send_spam(self):
        async with self.bot.exclusive_lock:
            while self.spam_msg_cnt > 0:
                self.bot.typer.send_message(self.spam_msg)
                self.spam_msg_cnt -= 1
                await asyncio.sleep(random.uniform(0.2, 0.5))
            self.spam_task_running = False

    async def on_bot_message_edit(self, message):
        if message.channel.id != self.bot.config["type_channel_id"]:
            return
        pass