import time
import random
from asyncio import Event


class CooldownHelper:
    COOLDOWN_TITLES = ["Slow it down, cmon", "Woah now, slow it down"]

    def __init__(self, cooldown_base):
        self.known_cooldown = None
        self.base = cooldown_base
        self.done_event = Event()

    def get_next_try_in(self):
        try_in = self.base
        if self.known_cooldown is not None:
            try_in = min(self.known_cooldown - time.time(), try_in)
        return CooldownHelper.get_cooldown_with_jitter(try_in)

    def on_send(self):
        self.done_event.clear()

    async def wait(self):
        await self.done_event.wait()

    def on_executed(self):
        self.known_cooldown = None
        self.done_event.set()

    def process_bot_message(self, message, cooldown_txt):
        c = CooldownHelper.extract_cooldown(message, cooldown_txt)
        if c is not None:
            self.known_cooldown = time.time() + c
            self.done_event.set()
            return True
        return False

    @staticmethod
    def extract_cooldown(msg, cdown_txt):
        if len(msg.embeds) != 1:
            return
        e = msg.embeds[0]
        if e.title in CooldownHelper.COOLDOWN_TITLES and e.description.startswith(cdown_txt + " **"):
            c = e.description[len(cdown_txt + " **"):]
            c, _, _ = c.partition(" second")
            return float(c)
        return None

    @staticmethod
    def get_cooldown_with_jitter(cooldown):
        if cooldown >= 30:
            return random.uniform(cooldown - 4, cooldown + 10)
        if cooldown >= 10:
            return random.uniform(cooldown - 2, cooldown + 5)
        return max(random.uniform(cooldown - 0.1, cooldown + 1), 0.5)

