import logging
import sys
from config import config
from bot import TheBot
from bot_beg import BegBot
from bot_search import SearchBot
from bot_meme import MemeBot
from bot_fish import FishBot
from bot_hunt import HuntBot
from bot_event import EventBot
from bot_gamble import GambleBot
from bot_blackjack import BlackjackBot
from bot_autodep import AutoDepBot

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(name)s %(message)s', stream=sys.stdout)
logging.getLogger("bot").setLevel(logging.DEBUG)

bot = TheBot(config)
bot.add_bot(BegBot(bot))
bot.add_bot(SearchBot(bot))
bot.add_bot(MemeBot(bot))
bot.add_bot(FishBot(bot))
bot.add_bot(HuntBot(bot))
bot.add_bot(EventBot(bot))
# bot.add_bot(GambleBot(bot))
# bot.add_bot(BlackjackBot(bot))
bot.add_bot(AutoDepBot(bot))
bot.run(config["token"])
bot.stop()