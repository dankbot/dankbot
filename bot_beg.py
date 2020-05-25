from bot_base import BotBase
from bot_util import *
import re


class BegBot(BotBase):
    P_REPLY_NORMAL = re.compile(f"^\\*\\*.*?\\*\\* has donated ([0-9,]+) coins to ({P_MENTION})!$")
    P_REPLY_ITEM = re.compile(f"^\\*\\*.*?\\*\\* has donated ([0-9,]+) coins to ({P_MENTION}), and a {P_SHOP_ICON} \\*\\*({P_SHOP_NAME})\\*\\*(?: WOW LUCKY)?$") #

    async def on_bot_message(self, message):
        r = BegBot.P_REPLY_NORMAL.match(message.content)
        if r and get_mention_user_id(r.group(2)) == self.bot.owner_id:
            self.bot.inventory.add_coins(int(r.group(1)), "beg")

        r = BegBot.P_REPLY_ITEM.match(message.content)
        if r and get_mention_user_id(r.group(2)) == self.bot.owner_id:
            self.bot.inventory.add_coins(int(r.group(1)), "beg")
            self.bot.inventory.add_item(r.group(3), 1, "beg")