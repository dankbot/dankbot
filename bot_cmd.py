from cmd_beg import BegHandler
from cmd_fish import FishHandler
from cmd_hunt import HuntHandler
from cmd_meme import PostMemeHandler
from cmd_search import SearchHandler


class BotCommandExecutor:
    def __init__(self, bot):
        self.bot = bot
        self.beg_handler = BegHandler(bot)
        self.fish_handler = FishHandler(bot)
        self.hunt_handler = HuntHandler(bot)
        self.meme_handler = PostMemeHandler(bot)
        self.search_handler = SearchHandler(bot)

    async def run_simple(self, handler):
        while True:
            b = await handler.new_execution()
            b.send_command()
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
