from bot_base import ActivatableSimpleBot
from bot_util import *
import re
import random


class MemeBot(ActivatableSimpleBot):
    P_REPLY = re.compile("^\\*\\*__What type of meme do you want to post?__\\*\\*\n")
    P_NO_ITEM = re.compile("^oi you need to buy a laptop in the shop to post memes" + P_EOL)
    P_MEME_DONE = re.compile("^Your meme got \\*\\*[0-9,]+ upvotes\\*\\*. You get ([0-9,]+) coins from the ads" + P_EOL)
    P_MEME_TRENDING = re.compile(f"^Your meme is \\*\\*__TRENDING__\\*\\* with \\*\\*[0-9,]+ karma\\*\\*. You get ([0-9,]+) coins, niceeee meme bro" + P_EOL)
    P_MEME_TRENDING_ITEM = re.compile(f"Your meme is \\*\\*__TRENDING__\\*\\* with \\*\\*[0-9,]+ karma\\*\\*. You get ([0-9,]+) coins, also a fan of your memes sent you ([0-9,]+) {P_SHOP_ICON} \\*\\*({P_SHOP_NAME})\\*\\*" + P_EOL)
    P_MEME_HATE = re.compile(f"^Everyone \\*\\*hates\\*\\* your meme, and it ended up with \\*\\*-[0-9,]+ karma\\*\\*. You get 0 coins lol sucks to be you" + P_EOL)
    P_MEME_LOST_LAPTOP = re.compile(f"^Everyone \\*\\*hates\\*\\* your meme, and it ended up with \\*\\*-[0-9,]+ karma\\*\\*. You get 0 coins AND now your :laptop: \\*\\*Laptop\\*\\* is broken lmao" + P_EOL)
    P_MEME_FAIL_OPT = re.compile("^That's not an option my friend" + P_EOL)
    COOLDOWN_TXT = "If you post memes too much, you look like a normie. Wait "

    def __init__(self, bot):
        super().__init__(bot, "meme", MemeBot.COOLDOWN_TXT)
        self.sent_meme_type = False

    async def send_command(self):
        self.bot.typer.send_message(self.bot.get_prefixed_cmd("pm"))
        if random.randint(0, 10) < 3:
            self.bot.typer.send_message("e")
        else:
            self.bot.typer.send_message("d")

    async def on_self_message(self, message):
        if self.is_activation_command(message):
            self.sent_meme_type = False
        if self.is_active(message.channel.id):
            self.sent_meme_type = True
        await super().on_self_message(message)

    def is_activation_command(self, message):
        return message.content == self.bot.get_prefixed_cmd("pm")

    async def process_bot_message(self, message):
        r = MemeBot.P_MEME_FAIL_OPT.match(message.content)
        if r:
            return True

        if not self.sent_meme_type:
            return False

        r = MemeBot.P_MEME_DONE.match(message.content)
        if r:
            self.bot.inventory.add_coins(parse_bot_int(r.group(1)), "meme")
            return True

        r = MemeBot.P_MEME_TRENDING.match(message.content)
        if r:
            self.bot.inventory.add_coins(parse_bot_int(r.group(1)), "meme")
            return True

        r = MemeBot.P_MEME_TRENDING_ITEM.match(message.content)
        if r:
            self.bot.inventory.add_coins(parse_bot_int(r.group(1)), "meme")
            self.bot.inventory.add_item(r.group(3), parse_bot_int(r.group(2)), "meme")
            return True

        r = MemeBot.P_MEME_HATE.match(message.content)
        if r:
            return True

        r = MemeBot.P_MEME_LOST_LAPTOP.match(message.content)
        if r:
            # consider the cost of the laptop as money lost
            self.bot.inventory.add_coins(-1500, "meme")
            return True

        if MemeBot.P_NO_ITEM.match(message.content):
            await self.bot.send_notify(f"prob get a laptop dude")
            return True

        return False
