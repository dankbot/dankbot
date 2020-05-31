from cmd_base import BaseExecution, BaseExecutionHandler
from cmd_util import *
import re
import random


class PostMemeExecution(BaseExecution):
    P_REPLY = re.compile("^\\*\\*__What type of meme do you want to post?__\\*\\*\n")
    P_NO_ITEM = re.compile("^oi you need to buy a laptop in the shop to post memes" + P_EOL)
    P_MEME_DONE = re.compile("^Your meme got \\*\\*[0-9,]+ upvotes\\*\\*. You get ([0-9,]+) coins from the ads" + P_EOL)
    P_MEME_TRENDING = re.compile(f"^Your meme is \\*\\*__TRENDING__\\*\\* with \\*\\*[0-9,]+ karma\\*\\*. You get ([0-9,]+) coins, niceeee meme bro" + P_EOL)
    P_MEME_TRENDING_ITEM = re.compile(f"Your meme is \\*\\*__TRENDING__\\*\\* with \\*\\*[0-9,]+ karma\\*\\*. You get ([0-9,]+) coins, also a fan of your memes sent you ([0-9,]+) {P_SHOP_ICON} \\*\\*({P_SHOP_NAME})\\*\\*" + P_EOL)
    P_MEME_HATE = re.compile(f"^Everyone \\*\\*hates\\*\\* your meme, and it ended up with \\*\\*-[0-9,]+ karma\\*\\*. You get 0 coins lol sucks to be you" + P_EOL)
    P_MEME_LOST_LAPTOP = re.compile(f"^Everyone \\*\\*hates\\*\\* your meme, and it ended up with \\*\\*-[0-9,]+ karma\\*\\*. You get 0 coins AND now your <:laptop:573151773565386819> \\*\\*Laptop\\*\\* is broken lmao" + P_EOL)
    P_MEME_FAIL_OPT = re.compile("^That's not an option my friend" + P_EOL)
    COOLDOWN_TXT = "If you post memes too much, you look like a normie. Wait "

    def __init__(self, handler):
        super().__init__(handler)
        self.cooldown_text = PostMemeExecution.COOLDOWN_TXT
        self.money = 0
        self.item = None
        self.item_count = 0
        self.lost_laptop = False
        self.no_laptop = False
        self.recv_meme_type = None

    def send_command(self, meme_type=None):
        if meme_type is None:
            if random.randint(0, 10) < 3:
                meme_type = "e"
            else:
                meme_type = "d"
        self.send_activation_message_as_user(self.bot.get_prefixed_cmd("pm"))
        self.send_message_as_user(meme_type)

    def on_user_message(self, message, is_activation):
        if not is_activation and self.recv_meme_type is None:
            self.recv_meme_type = message.content
            self.bump_timeout()

    async def on_bot_message(self, message):
        r = PostMemeExecution.P_MEME_FAIL_OPT.match(message.content)
        if r:
            return True

        if PostMemeExecution.P_NO_ITEM.match(message.content):
            self.no_laptop = True
            return True

        if self.recv_meme_type is None:
            return False

        r = PostMemeExecution.P_MEME_DONE.match(message.content)
        if r:
            self.money = parse_bot_int(r.group(1))
            self.bot.inventory.add_coins(self.money, "meme")
            return True

        r = PostMemeExecution.P_MEME_TRENDING.match(message.content)
        if r:
            self.money = parse_bot_int(r.group(1))
            self.bot.inventory.add_coins(self.money, "meme")
            return True

        r = PostMemeExecution.P_MEME_TRENDING_ITEM.match(message.content)
        if r:
            self.money = parse_bot_int(r.group(1))
            self.item = r.group(3)
            self.item_count = parse_bot_int(r.group(2))
            self.bot.inventory.add_coins(self.money, "meme")
            self.bot.inventory.add_item(self.item, self.item_count, "meme")
            return True

        r = PostMemeExecution.P_MEME_HATE.match(message.content)
        if r:
            return True

        r = PostMemeExecution.P_MEME_LOST_LAPTOP.match(message.content)
        if r:
            self.lost_laptop = True
            # consider the cost of the laptop as money lost
            self.bot.inventory.add_coins(-1500, "meme")
            return True

        return False

    def __str__(self):
        return f"PostMemeExecution: was_executed={self.was_executed} money={self.money} item={self.item} " \
               f"item_count={self.item_count} lost_laptop={self.lost_laptop} no_laptop={self.no_laptop} " \
               f"recv_meme_type={self.recv_meme_type}"


class PostMemeHandler(BaseExecutionHandler):
    def __init__(self, bot):
        super().__init__(bot, "meme")
        self.execution_factory = lambda: PostMemeExecution(self)
        self.requires_exclusivity = True

    def is_activation_command(self, message):
        return message.content == self.bot.get_prefixed_cmd("pm")
