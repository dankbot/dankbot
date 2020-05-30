from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re


class GambleExecution(BaseExecution):
    GAME_WON = re.compile(f"^You won \\*\\*([0-9,]+)\\*\\* coins\\. ?\n[^\n]+\n\nYou now have \\*\\*([0-9,]+)\\*\\* coins.$")
    GAME_LOST = re.compile(f"^You lost \\*\\*([0-9,]+)\\*\\* coins\\.\n\nYou now have \\*\\*([0-9,]+)\\*\\* coins.$")
    GAME_TIE = re.compile(f"^Tie! You lost \\*\\*([0-9,]+)\\*\\* coins\\. ?\n\nYou now have \\*\\*([0-9,]+)\\*\\* coins.$")
    GAME_NOT_ENOUGH_MONEY = re.compile(f"^You only have ([0-9,]+) coins, dont try and lie to me hoe\\." + P_EOL)
    COOLDOWN_TXT = "If I let you bet whenever you wanted, you'd be a lot more poor. Wait "

    def __init__(self, handler):
        super().__init__(handler)
        self.cooldown_text = GambleExecution.COOLDOWN_TXT
        self.gambled_money = 0
        self.gained_money = 0
        self.not_enough_money = False
        self.known_balance = None

    def send_command(self, money):
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd(f"gamble {money}"))

    def on_user_message(self, message, is_activation):
        if is_activation:
            str = self.bot.get_prefixed_cmd("gamble ")
            if message.content.startswith(str):
                self.gambled_money = int(message.content[len(str):])

    async def on_bot_message(self, message):
        r = GambleExecution.GAME_NOT_ENOUGH_MONEY.match(message.content)
        if r:
            self.not_enough_money = True
            self.known_balance = parse_bot_int(r.group(1))
            return True

        if message.content != "" or len(message.embeds) != 1:
            return False

        our_user = self.bot.get_user(self.bot.user_id)
        if message.embeds[0].author.name != our_user.name + "'s gambling game":
            return False

        r = GambleExecution.GAME_WON.match(message.embeds[0].description)
        if r:
            self.gained_money = parse_bot_int(r.group(1))
            self.known_balance = parse_bot_int(r.group(2))
            self.handler.total_won += 1
            self.handler.total_won_money += self.gained_money
            self.bot.inventory.add_coins(self.gained_money, "gamble")
            self.bot.inventory.set_total_coins(self.known_balance)
            return True

        r = GambleExecution.GAME_LOST.match(message.embeds[0].description)
        if r:
            self.gained_money = -parse_bot_int(r.group(1))
            self.known_balance = parse_bot_int(r.group(2))
            self.handler.total_lost += 1
            self.handler.total_lost_money += -self.gained_money
            self.bot.inventory.add_coins(self.gained_money, "gamble")
            self.bot.inventory.set_total_coins(self.known_balance)
            return True

        r = GambleExecution.GAME_TIE.match(message.embeds[0].description)
        if r:
            self.gained_money = -parse_bot_int(r.group(1))
            self.known_balance = parse_bot_int(r.group(2))
            self.handler.total_drawn += 1
            self.handler.total_drawn_money += -self.gained_money
            self.bot.inventory.add_coins(self.gained_money, "gamble")
            self.bot.inventory.set_total_coins(self.known_balance)
            return True

        return False

    def __str__(self):
        return f"GambleExecution: was_executed={self.was_executed} gambled_money={self.gambled_money} " \
               f"gained_money={self.gained_money} not_enough_money={self.not_enough_money} " \
               f"known_balance={self.known_balance}"


class GambleHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "gamble")
        self.execution_factory = lambda: GambleExecution(self)
        self.total_won = 0
        self.total_lost = 0
        self.total_drawn = 0
        self.total_won_money = 0
        self.total_lost_money = 0
        self.total_drawn_money = 0

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd("gamble "))
