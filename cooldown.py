import time
import random


class CooldownHelper:
    COOLDOWN_TITLES = ["Slow it down, cmon", "Woah now, slow it down"]
    COOLDOWN_TXT_GENERIC = ["You'll be able to use this command again in ", "This command can be used again in "]

    def __init__(self, cooldown_base):
        self.known_cooldown = None
        self.base = cooldown_base

    def get_wait_time(self):
        if self.known_cooldown is not None:
            r = self.known_cooldown - time.time()
            if r > 0:
                return CooldownHelper.get_cooldown_with_jitter(r)
        return 0

    def override_cooldown(self, time_from_now=None):
        if time_from_now is None:
            time_from_now = self.base
        self.known_cooldown = time.time() + time_from_now

    @staticmethod
    def extract_cooldown(msg, cdown_txt):
        if cdown_txt is None:
            for t in CooldownHelper.COOLDOWN_TXT_GENERIC:
                c = CooldownHelper.extract_cooldown(msg, t)
                if c is not None:
                    return c
            return None
        if len(msg.embeds) != 1:
            return None
        e = msg.embeds[0]
        if e.title in CooldownHelper.COOLDOWN_TITLES and e.description.startswith(cdown_txt + " **"):
            c = e.description[len(cdown_txt + " **"):]
            c, _, _ = c.partition(" second")
            return float(c)
        return None

    @staticmethod
    def get_cooldown_with_jitter(cooldown):
        if cooldown >= 30:
            return random.uniform(cooldown + 0.1, cooldown + 10)
        if cooldown >= 10:
            return random.uniform(cooldown + 0.1, cooldown + 5)
        return max(random.uniform(cooldown + 0.1, cooldown + 1), 0.5)

