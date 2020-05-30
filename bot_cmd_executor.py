from cmd_beg import BegHandler
from cmd_fish import FishHandler
from cmd_gamble import GambleHandler
from cmd_hunt import HuntHandler
from cmd_meme import PostMemeHandler
from cmd_search import SearchHandler
from cmd_inv import InventoryHandler
from cmd_gift import GiftHandler
from cmd_give import GiveHandler
from cmd_dep import DepositHandler
from cmd_withdraw import WithdrawHandler
from cmd_bal import BalanceHandler
from cmd_use import UseHandler
from cmd_trivia import TriviaHandler


class BotCommandExecutor:
    def __init__(self, bot):
        self.bot = bot
        self.beg_handler = BegHandler(bot)
        self.fish_handler = FishHandler(bot)
        self.hunt_handler = HuntHandler(bot)
        self.meme_handler = PostMemeHandler(bot)
        self.search_handler = SearchHandler(bot)
        self.inv_handler = InventoryHandler(bot)
        self.gift_handler = GiftHandler(bot)
        self.give_handler = GiveHandler(bot)
        self.dep_handler = DepositHandler(bot)
        self.withdraw_handler = WithdrawHandler(bot)
        self.bal_handler = BalanceHandler(bot)
        self.gamble_handler = GambleHandler(bot)
        self.use_handler = UseHandler(bot)
        self.trivia_handler = TriviaHandler(bot)

    async def run_simple(self, handler, *args):
        while True:
            b = await handler.new_execution()
            b.send_command(*args)
            await b
            if b.was_executed:
                return b

    async def beg(self):
        return await self.run_simple(self.beg_handler)

    async def fish(self):
        return await self.run_simple(self.fish_handler)

    async def hunt(self):
        return await self.run_simple(self.hunt_handler)

    async def post_meme(self):
        return await self.run_simple(self.meme_handler)

    async def search_with_preferences(self, preferences=None):
        if preferences is None:
            preferences = self.bot.config["search_preference"]
        while True:
            b = await self.search_handler.new_execution()
            b.send_command()
            if not await b.wait_for_areas():
                continue
            selection = "neither"
            for s in preferences:
                if s in b.areas:
                    selection = s
                    break
            b.send_area_selection(selection)
            await b
            if b.was_executed:
                return b

    async def inventory(self, page):
        return await self.run_simple(self.inv_handler, page)

    async def fetch_inventory(self):
        page1 = await self.inventory(1)
        assert page1.page == 1 and page1.total_pages < 10
        items = page1.items
        for p in range(2, page1.total_pages + 1):
            page = await self.inventory(p)
            items = items + page.items
        return items

    async def gift(self, what, count, who):
        return await self.run_simple(self.gift_handler, what, count, who)

    async def give(self, count, who):
        return await self.run_simple(self.give_handler, count, who)

    async def deposit(self, amount):
        return await self.run_simple(self.dep_handler, amount)

    async def withdraw(self, amount):
        return await self.run_simple(self.withdraw_handler, amount)

    async def balance(self, whose=None):
        return await self.run_simple(self.bal_handler, whose)

    async def gamble(self, amount):
        return await self.run_simple(self.gamble_handler, amount)

    async def use(self, what, count=None):
        return await self.run_simple(self.use_handler, what, count)

    async def trivia(self):
        while True:
            b = await self.trivia_handler.new_execution()
            b.send_command()
            if not await b.wait_for_question():
                continue
            b.send_answer("a")
            await b
            if b.was_executed:
                return b
