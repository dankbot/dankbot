import asyncio_rw_lock
from cmd_util import *
import re
import time
import asyncio
import random


class EventBot:
    P_REPLY_NORMAL = re.compile(f"^{P_SHOP_ICON} \\*\\*`[A-Z ]+ EVENT TIME WOO!`\\*\\*\n")
    P_TYPE_NORMAL = re.compile(f"^Type `(.*)`" + P_EOL)
    P_TYPE_BOSS = re.compile(f"^Attack the boss by typing `(.*)` into chat!" + P_EOL)
    P_HP_ZERO = re.compile("\n[0-9,]+ hits? — 0/[0-9,]+ HP" + P_EOL)
    P_EXPIRED = re.compile("\n<:red:573150416926408704> `This event has expired. No new submissions will be accepted.`" + P_EOL)

    def __init__(self, bot):
        self.bot = bot
        self.event_started_time = None
        self.event_msg_id = None
        self.event_msg2_id = None
        self.spam_msg = None
        self.spam_msg_cnt = 0
        self.spam_task_running = False

    def clear_active_event(self):
        self.spam_msg = None
        self.spam_msg_cnt = 0
        self.event_msg2_id = None

    async def on_user_message(self, message):
        if message.content != self.spam_msg:
            self.clear_active_event()

    async def on_bot_message(self, message):
        can_just_type = message.channel.id == self.bot.config["type_channel_id"]

        if EventBot.P_REPLY_NORMAL.match(message.content):
            self.event_started_time = time.time()
            self.event_msg_id = message.id

        if self.event_started_time is not None:
            if time.time() - self.event_started_time > 3:  # expire the event if follow up not within 3s
                self.event_started_time = None
                return

            r = EventBot.P_TYPE_NORMAL.match(message.content)
            if r:
                self.event_started_time = None
                self.event_msg2_id = message.id
                text = filter_ascii(r.group(1))
                if can_just_type:
                    self.start_send_spam(text, 1)
                if "event_notify" in self.bot.confg and self.bot.config["event_notify"]:
                    await self.bot.notify_channel_event.wait()
                    await self.bot.notify_channel.send("boss event in " + message.channel.mention + ": `" + text + "`")

            r = EventBot.P_TYPE_BOSS.match(message.content)
            if r:
                self.event_started_time = None
                self.event_msg2_id = message.id
                text = filter_ascii(r.group(1))
                if can_just_type:
                    self.start_send_spam(text, 10)
                if "event_notify" in self.bot.confg and self.bot.config["event_notify"]:
                    await self.bot.notify_channel_event.wait()
                    await self.bot.notify_channel.send("boss event in " + message.channel.mention + ": `" + text + "`")

    def start_send_spam(self, msg, cnt):
        self.spam_msg = msg
        self.spam_msg_cnt = cnt
        if not self.spam_task_running:
            self.spam_task_running = True
            asyncio.create_task(self.send_spam())

    async def send_spam(self):
        async with self.bot.exclusive_lock(asyncio_rw_lock.Read):
            while self.spam_msg_cnt > 0:
                self.bot.typer.send_message(self.spam_msg)
                self.spam_msg_cnt -= 1
                await asyncio.sleep(random.uniform(0.2, 0.5))
            self.spam_task_running = False

    async def on_bot_message_edit(self, message):
        if message.id != self.event_msg_id and message.id != self.event_msg2_id:
            return
        if EventBot.P_EXPIRED.match(message.content) and message.id == self.event_msg_id:
            self.clear_active_event()
        if EventBot.P_HP_ZERO.match(message.content) and message.id == self.event_msg2_id:
            self.clear_active_event()
