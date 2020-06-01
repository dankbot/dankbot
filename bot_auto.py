import asyncio
import logging
import time

from inventory import AsyncTotalListener
import random


class AutoBot:
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger("bot.auto")

    def start(self):
        m = self.bot.config["modules"] if "modules" in self.bot.config else []
        if "beg" in m:
            asyncio.create_task(self.auto_beg())
        if "search" in m:
            asyncio.create_task(self.auto_search())
        if "fish" in m:
            asyncio.create_task(self.auto_fish())
        if "hunt" in m:
            asyncio.create_task(self.auto_hunt())
        if "pm" in m:
            asyncio.create_task(self.auto_meme())
        if "gamble" in m:
            asyncio.create_task(self.auto_gamble())
        if "blackjack" in m:
            asyncio.create_task(self.auto_blackjack())
        if "trivia" in m:
            asyncio.create_task(self.auto_trivia())
        if "fidget" in m:
            asyncio.create_task(self.auto_fidget())
        if "depwit" in m:
            asyncio.create_task(self.auto_depwit())
        asyncio.create_task(self.auto_dep()) # will exit if disabled
        pass

    async def auto_beg(self):
        while True:
            await self.bot.cmd.beg()

    async def auto_search(self):
        while True:
            await self.bot.cmd.search_with_preferences()

    async def auto_fish(self):
        while True:
            await self.bot.cmd.fish()

    async def auto_hunt(self):
        while True:
            await self.bot.cmd.hunt()

    async def auto_meme(self):
        while True:
            r = await self.bot.cmd.post_meme()
            if r.no_laptop:
                r = await self.bot.cmd.buy("laptop")
                if not r.success:
                    await self.bot.send_notify(f"prob get a laptop dude as we couldn't get one")

    async def auto_gamble(self):
        while True:
            await self.bot.cmd.gamble(100)

    async def auto_blackjack(self):
        if "blahjack_exe" not in self.bot.config:
            self.log.error("blahjack not set, cannot play blackjack")
            return

        while True:
            await self.bot.cmd.blackjack(100)

    async def auto_trivia(self):
        while True:
            await self.bot.cmd.trivia()

    async def auto_fidget(self):
        while True:
            r = await self.bot.cmd.use("fidget")
            if r.already_in_use:
                r = await self.bot.cmd.profile()
                found = False
                for (name, expires) in r.active_items:
                    if name == "Fidget Spinner":
                        self.log.info(f"Spinner already in use, will last {expires} seconds")
                        await asyncio.sleep(expires + 5)
                        found = True
                        break
                if not found:
                    self.log.info("Spinner already in use, but we couldn't find it in profile??")
                    await asyncio.sleep(30)
            elif r.used:
                self.log.info(f"We used a spinner! It will last {r.fidget_time} seconds")
                await asyncio.sleep(r.fidget_time + 5)
            elif r.not_owned:
                self.log.info("Eww we have no spinner, buying one")
                await self.bot.cmd.buy("fidget")

    async def auto_depwit(self):
        while True:
            cooldown = time.time() + 30
            await self.bot.cmd.deposit(1)
            await self.bot.cmd.withdraw(1)
            r = cooldown - time.time()
            if r > 0:
                await asyncio.sleep(r)

    async def auto_dep(self):
        mode = self.bot.config["autodep_mode"]
        threshold_min, threshold_max = self.bot.config["autodep_threshold"]
        result_min, result_max = self.bot.config["autodep_result"]

        if mode not in ["give", "dep"]:
            return

        threshold = random.randint(threshold_min, threshold_max)
        self.log.info(f"Will auto-dep at {threshold}")

        l = AsyncTotalListener()
        self.bot.inventory.total_listeners.append(l)
        while True:
            await l.wait_for_update()
            if self.bot.inventory.total_coins <= threshold:
                continue
            b = await self.bot.cmd.balance()
            if b.wallet > threshold:
                threshold = random.randint(threshold_min, threshold_max)
                amount = b.wallet - random.randint(result_min, result_max)
                self.log.info(f"Next auto-dep threshold is {threshold}")
                if amount <= 0:
                    continue

                # try to round to 100
                try_values = [round(amount / 100) * 100, amount // 100 * 100, (amount + 99) // 100 * 100]
                for v in try_values:
                    if v >= result_min and v <= result_max:
                        amount = v
                        break

                self.log.info(f"Auto-depositing {amount} coins")

                if mode == "dep":
                    await self.bot.cmd.deposit(amount)
                elif mode == "give":
                    acc_id = self.bot.config["autodep_account_id"]
                    await self.bot.cmd.give(amount, f"<@{acc_id}>")

