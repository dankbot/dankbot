from bot_base import ActivatableSimpleBot
from bot_util import *
import re


class SearchBot(ActivatableSimpleBot):
    P_SEARCH_DONE = re.compile(f"^\\*\\*Area searched:\\*\\* `([A-Z]*)`\n.*([0-9]+) coins.*" + P_EOL)
    P_SEARCH_FAIL_GUESS = re.compile(f"^\\*\\*Area searched:\\*\\* `([A-Z]*)`\n.*" + P_EOL)
    P_SEARCH_FAIL_OPT = re.compile("^what are you THINKING man that's not a valid option from the list\\?\\?" + P_EOL)
    SEARCH_OPTIONS_TXT = "Where do you want to search? Pick from the list below and type it in chat.\n"
    COOLDOWN_TXT = "You've already scouted the area for coins, try again in "

    def __init__(self, bot):
        super().__init__(bot, "search", SearchBot.COOLDOWN_TXT)
        self.area_searched = None

    async def send_command(self):
        self.bot.typer.send_message(self.bot.get_prefixed_cmd("search"))

    def is_activation_command(self, message):
        return message.content == self.bot.get_prefixed_cmd("search")

    async def on_self_message(self, message):
        if self.is_activation_command(message):
            self.area_searched = None
        if self.is_active(message.channel.id):
            self.area_searched = message.content.upper()
        await super().on_self_message(message)

    async def process_bot_message(self, message):
        if message.content.startswith(SearchBot.SEARCH_OPTIONS_TXT):
            options, _, _ = message.content[len(SearchBot.SEARCH_OPTIONS_TXT):].partition("\n")
            options = options.split(", ")
            options = [o[1:-1] for o in options if len(o) > 0 and o[0] == '`' and o[-1] == '`']
            for s in self.bot.config["search_preference"]:
                if s in options:
                    self.bot.typer.send_message(s)
                    return False
            self.bot.typer.send_message("neither")
            return False

        r = SearchBot.P_SEARCH_DONE.match(message.content)
        if r and r.group(1) == self.area_searched:
            self.bot.inventory.add_coins(int(r.group(2)), "search")
            return True

        r = SearchBot.P_SEARCH_FAIL_GUESS.match(message.content)
        if r and r.group(1) == self.area_searched:
            return True

        if SearchBot.P_SEARCH_FAIL_OPT.match(message.content):
            return True

        return False

