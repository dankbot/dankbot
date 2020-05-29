import asyncio


class AutoBot:
    def __init__(self, bot):
        self.bot = bot

    def start(self):
        asyncio.create_task(self.auto_beg())
        asyncio.create_task(self.auto_search())
        asyncio.create_task(self.auto_fish())
        asyncio.create_task(self.auto_hunt())
        asyncio.create_task(self.auto_meme())
        if self.bot.config["autogive_enabled"]:
            asyncio.create_task(self.auto_give())

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
            await self.bot.cmd.post_meme()

    async def auto_give(self):
        threshold = self.bot.config["autogive_threshold"]
        acc_id = self.bot.config["autogive_account_id"]
        if self.bot.user_id == acc_id:
            return
        while True:
            b = await self.bot.cmd.balance()
            if b.wallet > threshold:
                await self.bot.cmd.give(b.wallet - threshold, f"<@!{acc_id}>")
            await asyncio.sleep(100)  # wait 100 seconds

