from bot_base import ActivatableSimpleBot
from bot_util import *


class GambleBot(ActivatableSimpleBot):
    GAME_WON = re.compile(f"^You won \\*\\*([0-9,]+)\\*\\* coins\\. ?\n")
    GAME_LOST = re.compile(f"^You lost \\*\\*([0-9,]+)\\*\\* coins\\.\n")
    GAME_TIE = re.compile(f"^Tie! You lost \\*\\*([0-9,]+)\\*\\* coins\\. ?\n")
    COOLDOWN_TXT = "If I let you bet whenever you wanted, you'd be a lot more poor. Wait "

    def __init__(self, bot):
        super().__init__(bot, "gamble", GambleBot.COOLDOWN_TXT)
        self.won = 0
        self.lost = 0
        self.draw = 0
        self.won_money = 0
        self.lost_money = 0
        self.draw_lost_money = 0

    async def send_command(self):
        self.bot.typer.send_message(self.bot.get_prefixed_cmd(f"gamble 100"))

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd("gamble "))

    async def process_bot_message(self, message):
        if message.content != "" or len(message.embeds) != 1:
            return False

        our_user = self.bot.get_user(self.bot.user_id)
        if message.embeds[0].author.name != our_user.name + "'s gambling game":
            return False

        r = GambleBot.GAME_WON.match(message.embeds[0].description)
        if r:
            self.won += 1
            self.won_money += parse_bot_int(r.group(1))
            self.bot.inventory.add_coins(parse_bot_int(r.group(1)), "gamble")
            return True

        r = GambleBot.GAME_LOST.match(message.embeds[0].description)
        if r:
            self.lost += 1
            self.lost_money += parse_bot_int(r.group(1))
            self.bot.inventory.add_coins(-parse_bot_int(r.group(1)), "gamble")
            return True

        r = GambleBot.GAME_TIE.match(message.embeds[0].description)
        if r:
            self.draw += 1
            self.draw_lost_money += parse_bot_int(r.group(1))
            self.bot.inventory.add_coins(-parse_bot_int(r.group(1)), "gamble")
            return True

        return False

