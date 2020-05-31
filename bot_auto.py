import asyncio
import logging

from inventory import AsyncTotalListener
import random


class AutoBot:
    def __init__(self, bot):
        self.bot = bot
        self.log = logging.getLogger("bot.auto")

    def start(self):
        asyncio.create_task(self.auto_beg())
        asyncio.create_task(self.auto_search())
        asyncio.create_task(self.auto_fish())
        asyncio.create_task(self.auto_hunt())
        asyncio.create_task(self.auto_meme())
        asyncio.create_task(self.auto_gamble())
        asyncio.create_task(self.auto_blackjack())
        asyncio.create_task(self.auto_trivia())
        asyncio.create_task(self.auto_dep())
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

