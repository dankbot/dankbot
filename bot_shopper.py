from bot_base import SimpleTaskBot
from bot_util import *
import re


class ShopperBot(SimpleTaskBot):
    T_NOT_IN_SHOP = "what are you thinking tbh that item isn't even in the shop"
    T_EMPTY_WALLET = "your wallet is empty, go withdraw some BANK money to make this purchase"
    T_NOT_ENOUGH_MONEY = "Far out, you don't have enough money in your wallet or your bank to buy that much!!"
    P_SUCCESS = re.compile(f"^You bought ([0-9,]+) \\*\\*{P_SHOP_NAME}\\*\\* and paid `[0-9,]+ coins`" + P_EOL)

    def __init__(self, bot):
        super().__init__(bot, "shop", None)

    async def add(self, what, count):
        return await self.execute((what, count))

    def send_task_command(self, task):
        (task_what, task_count) = task
        self.bot.typer.send_message(self.bot.get_prefixed_cmd(f"buy {task_what} {task_count}"))

    def is_activation_command(self, message):
        return message.content.startswith(self.bot.get_prefixed_cmd(f"buy "))

    async def process_task_bot_message(self, task, message):
        if message.content in [ShopperBot.T_EMPTY_WALLET, ShopperBot.T_NOT_IN_SHOP, ShopperBot.T_NOT_ENOUGH_MONEY]:
            return False

        if message.content != "" or len(message.embeds) != 1:
            return

        e = message.embeds[0]
        if e.author.name == "Successful purchase":
            r = ShopperBot.P_SUCCESS.match(e.description)
            (_, task_count) = task
            if r and parse_bot_int(r.group(1)) == task_count:
                return True

        return None

