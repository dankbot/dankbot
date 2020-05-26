from bot_base import ActivatableSimpleBot
from bot_util import *
import json
from discord import Embed
from blahjack import run_blahjack
from collections import OrderedDict


class BlackjackBot(ActivatableSimpleBot):
    GAME_OPTIONS_HINT = "What do you want to do?\nType `h` to **hit**, type `s` to **stand**, or type `e` to **end** the game."
    GAME_OPTIONS_HINT2 = "Type `h` to **hit**, type `s` to **stand**, or type `e` to **end** the game."
    GAME_WON = re.compile(f"^\\*\\*You win! You have [0-9]*, Dealer has [0-9]*\\.\\*\\* \nYou won \\*\\*([0-9,]+)\\*\\* coins\\. You now have [0-9,]+\\." + P_EOL)
    GAME_WON_BUSTED = re.compile(f"\\*\\*You win! Your opponent busted!\\*\\* \nYou won \\*\\*([0-9,]+)\\*\\* coins\\. You now have [0-9,]+\\." + P_EOL)
    GAME_WON_21 = re.compile(f"\\*\\*You win! You have 21!\\*\\* \nYou won \\*\\*([0-9,]+)\\*\\* coins\\. You now have [0-9,]+\\." + P_EOL)
    GAME_WON_5CARDS = re.compile(f"\\*\\*You win! You took 5 cards without going over 21.\\*\\* \nYou won \\*\\*([0-9,]+)\\*\\* coins\\. You now have [0-9,]+\\." + P_EOL)
    GAME_LOST_LOWER = re.compile(f"^\\*\\*You lose! You have [0-9]*, Dealer has [0-9]*\\.\\*\\* You lost \\*\\*([0-9,]+)\\*\\* coins\\. You now have [0-9,]+\\." + P_EOL)
    GAME_LOST_BUSTED = re.compile(f"^\\*\\*You lose! Busted!\\*\\* You lost \\*\\*([0-9,]+)\\*\\* coins\\. You now have [0-9,]+\\." + P_EOL)
    GAME_LOST_21 = re.compile(f"^\\*\\*You lose! Your opponent reached 21 before you!\\.\\*\\* You lost \\*\\*([0-9,]+)\\*\\* coins\\. You now have [0-9,]+\\." + P_EOL)
    GAME_TIE = re.compile(f"^\\*\\*You tied with your opponent!\\*\\* Your wallet hasn't changed! You have [0-9,]+ coins still." + P_EOL)
    GAME_END = re.compile("^you ended the game" + P_EOL)
    GAME_INVALID_ARG = re.compile("^ur an idiot you need to give a valid response" + P_EOL)
    CARD_TOTAL = re.compile("^Total - `([0-9]+)`$")
    CARD_TOTAL_UNKNOWN = "Total - ` ? `"
    COOLDOWN_TXT = "If I let you bet whenever you wanted, you'd be a lot more poor. Wait "

    def __init__(self, bot):
        super().__init__(bot, "blackjack", BlackjackBot.COOLDOWN_TXT)
        self.current_game = []
        self.stake = 0
        self.game_writer = open("tmp/games.txt", "a+")

        self.outcomes = OrderedDict()
        for t in ["won", "won_busted","won_21", "won_5cards", "lost", "lost_busted", "lost_21", "tied"]:
            self.outcomes[t] = 0
        self.money_won = 0

    def end_game(self, outcome, money_outcome):
        self.outcomes[outcome] += 1
        self.money_won += money_outcome
        dict = {
            "outcome": outcome,
            "money_outcome": money_outcome,
            "transcript": self.current_game
        }
        json.dump(dict, self.game_writer, ensure_ascii=False)
        self.game_writer.write('\n')
        self.game_writer.flush()
        self.current_game = []

    async def send_command(self):
        self.bot.typer.send_message(self.bot.get_prefixed_cmd("bj 100"))

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd("bj "))

    async def on_self_message(self, message):
        if self.is_activation_command(message):
            self.stake = int(message.content[len(self.bot.get_prefixed_cmd("bj ")):])
            # cooldown is counted from the execution of this command instead of game end in case of blackjack
            self.cooldown.override_cooldown(self.cooldown.base)
        if len(self.current_game) > 0:
            if message.content == "h":
                self.current_game[-1]["decision"] = "hit"
            if message.content == "s":
                self.current_game[-1]["decision"] = "stand"
            if message.content == "e":
                self.current_game[-1]["decision"] = "exit"
        await super().on_self_message(message)

    @staticmethod
    def parse_cards(str):
        if not str.startswith("Cards - **"):
            return None
        str = str[len("Cards - **"):]
        str, _, total = str.partition("**\n")
        if total == BlackjackBot.CARD_TOTAL_UNKNOWN:
            total = None
        else:
            r = BlackjackBot.CARD_TOTAL.match(total)
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


    async def process_bot_message(self, message):
        if BlackjackBot.GAME_END.match(message.content):
            self.end_game("end", -self.stake/2)
            return True

        if message.content not in ["", BlackjackBot.GAME_OPTIONS_HINT, BlackjackBot.GAME_OPTIONS_HINT2]:
            return False
        if len(message.embeds) != 1:
            return False

        e = message.embeds[0]
        our_user = self.bot.get_user(self.bot.owner_id)
        if e.author.name != our_user.name + "'s blackjack game":
            return False

        if len(e.fields) == 2 and e.fields[0].name == our_user.name and e.fields[1].name == "Dank Memer":
            our_card_info = BlackjackBot.parse_cards(e.fields[0].value)
            bot_card_info = BlackjackBot.parse_cards(e.fields[1].value)
            if our_card_info is None or bot_card_info is None:
                return False
            our_cards, our_total = our_card_info
            bot_cards, bot_total = bot_card_info
            self.current_game.append({
                "our_cards": our_cards,
                "our_total": our_total,
                "bot_cards": bot_cards,
                "bot_total": bot_total
            })
            self.reset_timeout()

            if e.description == Embed.Empty:
                chance_hit, chance_stand = await run_blahjack(self.bot.config["blahjack_exe"], our_cards, bot_cards, len(self.current_game))
                self.log.info(f"Hit: {chance_hit}; Stand: {chance_stand}")
                await message.channel.send(f"Hit: {chance_hit}; Stand: {chance_stand}")
                if chance_hit > 0.3 and chance_hit > chance_stand:
                    self.bot.typer.send_message("h")
                elif chance_stand > 0.3:
                    self.bot.typer.send_message("s")
                else:
                    self.bot.typer.send_message("e")

        if e.description == Embed.Empty:
            return

        r = BlackjackBot.GAME_WON.match(e.description)
        if r:
            self.end_game("won", parse_bot_int(r.group(1)))
            return True

        r = BlackjackBot.GAME_WON_BUSTED.match(e.description)
        if r:
            self.end_game("won_busted", parse_bot_int(r.group(1)))
            return True

        r = BlackjackBot.GAME_WON_21.match(e.description)
        if r:
            self.end_game("won_21", parse_bot_int(r.group(1)))
            return True

        r = BlackjackBot.GAME_WON_5CARDS.match(e.description)
        if r:
            self.end_game("won_5cards", parse_bot_int(r.group(1)))
            return True

        r = BlackjackBot.GAME_LOST_LOWER.match(e.description)
        if r:
            self.end_game("lost", -parse_bot_int(r.group(1)))
            return True

        r = BlackjackBot.GAME_LOST_BUSTED.match(e.description)
        if r:
            self.end_game("lost_busted", -parse_bot_int(r.group(1)))
            return True

        r = BlackjackBot.GAME_LOST_21.match(e.description)
        if r:
            self.end_game("lost_21", -parse_bot_int(r.group(1)))
            return True

        r = BlackjackBot.GAME_TIE.match(e.description)
        if r:
            self.end_game("tied", 0)
            return True

        return False

