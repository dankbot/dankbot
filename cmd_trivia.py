from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re
import asyncio


class TriviaExecution(BaseExecution):
    T_TIMEOUT = "You did not answer in time, what the heck??"
    P_WRONG_ANSWER = re.compile(f"no [a-z\\- ]+, the correct answer was `.*`" + P_EOL)  #idiot|twit|nitwit|bonehead|blockhead|ignoramus|moron|ninny|stupid|simpleton
    P_CORRECT_ANSWER = re.compile(f"^correct [a-z\\- ]+, you earned \\*\\*([0-9,]+)\\*\\* coins" + P_EOL)  #smartass|large brain|genius

    def __init__(self, handler):
        super().__init__(handler)
        self.money = 0
        self.question = None
        self.answers = []
        self.question_event = asyncio.Event()
        self.recv_answer = None

    def send_command(self):
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd("trivia"))

    def send_answer(self, answer):
        self.send_message_as_user(answer)

    async def wait_for_question(self):
        await asyncio.wait([self.question_event.wait(), self], return_when=asyncio.FIRST_COMPLETED)
        return not self.completion_future.done()

    def on_user_message(self, message, is_activation):
        if not is_activation and self.recv_answer is None:
            self.recv_answer = message.content.lower()
            self.bump_timeout()

    async def on_bot_message(self, message):
        if self.recv_answer is not None:
            if message.content == TriviaExecution.T_TIMEOUT:
                return True
            if TriviaExecution.P_WRONG_ANSWER.match(message.content):
                return True
            r = TriviaExecution.P_CORRECT_ANSWER.match(message.content)
            if r:
                self.money = parse_bot_int(r.group(1))
                self.bot.inventory.add_coins(self.money, "trivia")
                return True

            return False

        if message.content != "" or len(message.embeds) != 1:
            return False

        our_user = self.bot.get_user(self.bot.user_id)
        if message.embeds[0].author.name != our_user.name + "'s trivia question":
            return False

        lines = message.embeds[0].description.split("\n")
        if len(lines) != 7 or not lines[0].startswith("**") or not lines[0].endswith("**"):
            return False
        if not lines[3].startswith("A) ") or not lines[4].startswith("B) ") or not lines[5].startswith("C) ") \
                or not lines[6].startswith("D) "):
            return False

        def unstyle(s):
            if len(s) > 0 and s[0] == '*' and s[-1] == '*':
                return s[1:-1]
            return s

        self.question = lines[0][2:-2]
        self.answers = [unstyle(s) for s in [lines[3][3:], lines[4][3:], lines[5][3:], lines[6][3:]]]
        self.question_event.set()

        return False

    def __str__(self):
        return f"TriviaExecution: was_executed={self.was_executed} question={self.question} answers={self.answers} " \
               f"recv_answer={self.recv_answer} money={self.money}"


class TriviaHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "trivia")
        self.execution_factory = lambda: TriviaExecution(self)
        self.requires_exclusivity = True

    def is_activation_command(self, message):
        return message.content == self.bot.get_prefixed_cmd("trivia")
