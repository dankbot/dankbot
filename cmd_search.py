from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re
import asyncio


class SearchExecution(BaseExecution):
    P_SEARCH_DONE = re.compile(f"^\\*\\*Area searched:\\*\\* `([A-Z]*)`\n.*?([0-9,]+) coins.*" + P_EOL)
    P_SEARCH_FAIL_GUESS = re.compile(f"^\\*\\*Area searched:\\*\\* `([A-Z]*)`\n.*" + P_EOL)
    P_SEARCH_FAIL_OPT = re.compile("^what are you THINKING man that's not a valid option from the list\\?\\?" + P_EOL)
    SEARCH_OPTIONS_TXT = "Where do you want to search? Pick from the list below and type it in chat.\n"
    COOLDOWN_TXT = "You've already scouted the area for coins, try again in "

    def __init__(self, handler):
        super().__init__(handler)
        self.cooldown_text = SearchExecution.COOLDOWN_TXT
        self.money = 0
        self.areas = []
        self.areas_event = asyncio.Event()
        self.recv_area = None

    def send_command(self):
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd("search"))

    def send_area_selection(self, area):
        self.send_message_as_user(area)

    async def wait_for_areas(self):
        await asyncio.wait([self.areas_event.wait(), self], return_when=asyncio.FIRST_COMPLETED)
        return not self.completion_future.done()

    def on_user_message(self, message, is_activation):
        if not is_activation and self.recv_area is None:
            self.recv_area = message.content.lower()
            self.bump_timeout()

    async def on_bot_message(self, message):
        if message.content.startswith(SearchExecution.SEARCH_OPTIONS_TXT):
            options, _, _ = message.content[len(SearchExecution.SEARCH_OPTIONS_TXT):].partition("\n")
            options = options.split(", ")
            options = [o[1:-1] for o in options if len(o) > 0 and o[0] == '`' and o[-1] == '`']
            self.areas = options
            self.areas_event.set()
            return False

        r = SearchExecution.P_SEARCH_DONE.match(message.content)
        if r and r.group(1).lower() == self.recv_area:
            self.money = parse_bot_int(r.group(2))
            self.bot.inventory.add_coins(self.money, "search")
            return True

        r = SearchExecution.P_SEARCH_FAIL_GUESS.match(message.content)
        if r and r.group(1) == self.recv_area:
            return True

        if SearchExecution.P_SEARCH_FAIL_OPT.match(message.content):
            return True

        return False

    def __str__(self):
        return f"SearchExecution: was_executed={self.was_executed} areas={self.areas} recv_area={self.recv_area} " \
               f"money={self.money}"


class SearchHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "search")
        self.execution_factory = lambda: SearchExecution(self)

    def is_activation_command(self, message):
        return message.content == self.bot.get_prefixed_cmd("search")
