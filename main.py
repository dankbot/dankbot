import logging
import sys
from config import config
from bot import TheBot
from bot_beg import BegBot
from bot_fish import FishBot
from bot_hunt import HuntBot

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', stream=sys.stdout)
logging.getLogger("bot").setLevel(logging.DEBUG)

bot = TheBot(config)
bot.add_bot(BegBot(bot))
bot.add_bot(FishBot(bot))
bot.add_bot(HuntBot(bot))
bot.run(config["token"])
bot.stop()