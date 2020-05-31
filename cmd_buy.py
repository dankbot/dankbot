from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re


class BuyExecution(BaseExecution):
    T_BAD_ITEM = "what are you thinking tbh that item isn't even in the shop"
    T_INVALID_NUMBER = "Are you stupid you can't sell less than 1 of something lol"
    T_NOT_ENOUGH_MONEY = "Far out, you don't have enough money in your wallet or your bank to buy that much!!"
    P_LIMIT = re.compile("^Do you really need more than [0-9,]+ of these? You have [0-9,]+ right now." + P_EOL)
    P_EXEC_WITH_NUMBER = re.compile("^(.*?) ([0-9]+)$")
    P_SUCCESS = re.compile(f"^You bought ([0-9,]+) \\*\\*({P_SHOP_NAME})\\*\\* and paid `([0-9,]+) coins?`$")

    def __init__(self, handler):
        super().__init__(handler)
        self.request_item = None
        self.item = None
        self.item_count = 0
        self.cost = 0
        self.success = False

    def send_command(self, item, amount=None):
        amount_t = f" {amount}" if amount is not None else ""
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd(f"buy {item}{amount_t}"))

    def on_user_message(self, message, is_activation):
        if is_activation:
            str = self.bot.get_prefixed_cmd("buy ")
            if message.content.startswith(str):
                c = message.content[len(str):]
                r = BuyExecution.P_EXEC_WITH_NUMBER.match(c)
                if r:
                    self.request_item = r.group(1)
                    self.item_count = int(r.group(2))
                else:
                    self.request_item = c
                    self.item_count = 1


    async def on_bot_message(self, message):
        if message.content in [BuyExecution.T_BAD_ITEM, BuyExecution.T_INVALID_NUMBER, BuyExecution.T_NOT_ENOUGH_MONEY]:
            return True

        if BuyExecution.P_LIMIT.match(message.content):
            return True

        if message.content != "" or len(message.embeds) != 1:
            return False
        if message.embeds[0].author.name != "Successful purchase":
            return False

        r = BuyExecution.P_SUCCESS.match(message.embeds[0].description)
        if r and parse_bot_int(r.group(1)) == self.item_count:
            self.item = r.group(2)
            self.cost = parse_bot_int(r.group(3))
            self.success = True
            return True

        return False

    def __str__(self):
        return f"BuyExecution: was_executed={self.was_executed} requested_item={self.request_item} item={self.item} " \
               f"item_count={self.item_count} cost={self.cost} success={self.success}"


class BuyHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "buy")
        self.execution_factory = lambda: BuyExecution(self)

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd("buy "))
