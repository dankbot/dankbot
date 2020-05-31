from collections import OrderedDict

from discord import Embed

from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re
import asyncio


class BlackjackExecution(BaseExecution):
    GAME_OPTIONS_HINT = "What do you want to do?\nType `h` to **hit**, type `s` to **stand**, or type `e` to **end** the game."
    GAME_OPTIONS_HINT2 = "Type `h` to **hit**, type `s` to **stand**, or type `e` to **end** the game."
    GAME_NOT_ENOUGH_MONEY = re.compile(f"^You only have [0-9,]+ coins, dont try and lie to me hoe\\." + P_EOL)
    GAME_WON = re.compile(f"^\\*\\*You win! You have [0-9]*, Dealer has [0-9]*\\.\\*\\* \nYou won \\*\\*([0-9,]+)\\*\\* coins\\. You now have ([0-9,]+)\\." + P_EOL)
    GAME_WON_BUSTED = re.compile(f"\\*\\*You win! Your opponent busted!\\*\\* \nYou won \\*\\*([0-9,]+)\\*\\* coins\\. You now have ([0-9,]+)\\." + P_EOL)
    GAME_WON_21 = re.compile(f"\\*\\*You win! You have 21!\\*\\* \nYou won \\*\\*([0-9,]+)\\*\\* coins\\. You now have ([0-9,]+)\\." + P_EOL)
    GAME_WON_5CARDS = re.compile(f"\\*\\*You win! You took 5 cards without going over 21.\\*\\* \nYou won \\*\\*([0-9,]+)\\*\\* coins\\. You now have ([0-9,]+)\\." + P_EOL)
    GAME_LOST_LOWER = re.compile(f"^\\*\\*You lose! You have [0-9]*, Dealer has [0-9]*\\.\\*\\* You lost \\*\\*([0-9,]+)\\*\\* coins\\. You now have ([0-9,]+)\\." + P_EOL)
    GAME_LOST_BUSTED = re.compile(f"^\\*\\*You lose! Busted!\\*\\* You lost \\*\\*([0-9,]+)\\*\\* coins\\. You now have ([0-9,]+)\\." + P_EOL)
    GAME_LOST_21 = re.compile(f"^\\*\\*You lose! Your opponent reached 21 before you!\\*\\* You lost \\*\\*([0-9,]+)\\*\\* coins\\. You now have ([0-9,]+)\\." + P_EOL)
    GAME_TIE = re.compile(f"^\\*\\*You tied with your opponent!\\*\\* Your wallet hasn't changed! You have ([0-9,]+) coins still." + P_EOL)
    GAME_END = re.compile("^you ended the game" + P_EOL)
    GAME_INVALID_ARG = re.compile("^ur an idiot you need to give a valid response" + P_EOL)
    CARD_TOTAL = re.compile("^Total - `([0-9]+)`$")
    CARD_TOTAL_UNKNOWN = "Total - ` ? `"
    COOLDOWN_TXT = "If I let you bet whenever you wanted, you'd be a lot more poor. Wait "

    def __init__(self, handler):
        super().__init__(handler)
        self.cooldown_text = BlackjackExecution.COOLDOWN_TXT
        self.gambled_money = 0
        self.gained_money = 0
        self.not_enough_money = False
        self.known_balance = None
        self.rounds = []
        self.outcome = None
        self.round_event = asyncio.Event()

    def send_command(self, money):
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd(f"bj {money}"))

    def send_decision(self, decision):
        self.round_event.clear()
        self.send_message_as_user(decision)

    async def wait_for_round(self):
        await asyncio.wait([self.round_event.wait(), self], return_when=asyncio.FIRST_COMPLETED)
        return not self.completion_future.done()

    def on_user_message(self, message, is_activation):
        if is_activation:
            for p in ["blackjack ", "bj "]:
                str = self.bot.get_prefixed_cmd(p)
                if message.content.startswith(str):
                    self.gambled_money = int(message.content[len(str):])
        else:
            if len(self.rounds) > 0:
                if message.content == "h":
                    self.rounds[-1]["decision"] = "hit"
                if message.content == "s":
                    self.rounds[-1]["decision"] = "stand"
                if message.content == "e":
                    self.rounds[-1]["decision"] = "exit"

    def end_game(self, outcome, money_outcome, known_balance=None):
        self.outcome = outcome
        self.gained_money = money_outcome
        self.known_balance = known_balance
        self.bot.inventory.add_coins(money_outcome, "blackjack")
        if known_balance is not None:
            self.bot.inventory.set_total_coins(known_balance)
        self.handler.on_game_ended(self)

    @staticmethod
    def parse_cards(str):
        if not str.startswith("Cards - **"):
            return None
        str = str[len("Cards - **"):]
        str, _, total = str.partition("**\n")
        if total == BlackjackExecution.CARD_TOTAL_UNKNOWN:
            total = None
        else:
            r = BlackjackExecution.CARD_TOTAL.match(total)
            if not r:
                return None
            total = int(r.group(1))
        arr = str.split("  ")
        for i in range(len(arr)):
            if arr[i] == "`?`":
                arr[i] = "?"
                continue
            if not arr[i].startswith("[`") or not arr[i].endswith(")"):
                return None
            arr[i], _, _ = arr[i][2:].partition("`](")
            if len(arr[i]) == 0:
                return None
        return arr, total

    async def on_bot_message(self, message):
        if BlackjackExecution.GAME_END.match(message.content):
            self.end_game("end", -self.gambled_money//2)
            return True
        if BlackjackExecution.GAME_NOT_ENOUGH_MONEY.match(message.content):
            self.not_enough_money = True
            return True

        if message.content not in ["", BlackjackExecution.GAME_OPTIONS_HINT, BlackjackExecution.GAME_OPTIONS_HINT2]:
            return False
        if len(message.embeds) != 1:
            return False

        e = message.embeds[0]
        our_user = self.bot.get_user(self.bot.user_id)
        if e.author.name != our_user.name + "'s blackjack game":
            return False

        if len(e.fields) == 2 and e.fields[0].name == our_user.name and e.fields[1].name == "Dank Memer":
            our_card_info = BlackjackExecution.parse_cards(e.fields[0].value)
            bot_card_info = BlackjackExecution.parse_cards(e.fields[1].value)
            if our_card_info is None or bot_card_info is None:
                return False
            our_cards, our_total = our_card_info
            bot_cards, bot_total = bot_card_info
            self.rounds.append({
                "our_cards": our_cards,
                "our_total": our_total,
                "bot_cards": bot_cards,
                "bot_total": bot_total
            })
            self.bump_timeout()

            if e.description == Embed.Empty:
                self.round_event.set()

        if e.description == Embed.Empty:
            return

        r = BlackjackExecution.GAME_WON.match(e.description)
        if r:
            self.end_game("won", parse_bot_int(r.group(1)), parse_bot_int(r.group(2)))
            return True

        r = BlackjackExecution.GAME_WON_BUSTED.match(e.description)
        if r:
            self.end_game("won_busted", parse_bot_int(r.group(1)), parse_bot_int(r.group(2)))
            return True

        r = BlackjackExecution.GAME_WON_21.match(e.description)
        if r:
            self.end_game("won_21", parse_bot_int(r.group(1)), parse_bot_int(r.group(2)))
            return True

        r = BlackjackExecution.GAME_WON_5CARDS.match(e.description)
        if r:
            self.end_game("won_5cards", parse_bot_int(r.group(1))), parse_bot_int(r.group(2))
            return True

        r = BlackjackExecution.GAME_LOST_LOWER.match(e.description)
        if r:
            self.end_game("lost", -parse_bot_int(r.group(1)), parse_bot_int(r.group(2)))
            return True

        r = BlackjackExecution.GAME_LOST_BUSTED.match(e.description)
        if r:
            self.end_game("lost_busted", -parse_bot_int(r.group(1)), parse_bot_int(r.group(2)))
            return True

        r = BlackjackExecution.GAME_LOST_21.match(e.description)
        if r:
            self.end_game("lost_21", -parse_bot_int(r.group(1)), parse_bot_int(r.group(2)))
            return True

        r = BlackjackExecution.GAME_TIE.match(e.description)
        if r:
            self.end_game("tied", 0, parse_bot_int(r.group(1)))
            return True

        return False

    def __str__(self):
        return f"BlackjackExecution: was_executed={self.was_executed} gambled_money={self.gambled_money} " \
               f"gained_money={self.gained_money} outcome={self.outcome} rounds={self.rounds} " \
               f"not_enough_money={self.not_enough_money} known_balance={self.known_balance} "


class BlackjackHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "blackjack")
        self.execution_factory = lambda: BlackjackExecution(self)
        self.requires_exclusivity = True

        self.outcomes = OrderedDict()
        for t in ["won", "won_busted", "won_21", "won_5cards", "lost", "lost_busted", "lost_21", "tied", "end", "timeout"]:
            self.outcomes[t] = 0
        self.total_won = 0
        self.total_lost = 0

    def on_game_ended(self, e):
        self.outcomes[e.outcome] += 1
        if e.gained_money >= 0:
            self.total_won += e.gained_money
        else:
            self.total_lost -= e.gained_money


    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd("bj ")) or \
               message.content.startswith(self.bot.get_prefixed_cmd("blackjack "))
