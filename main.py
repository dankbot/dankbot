import logging
import sys
from bot import TheBot

if len(sys.argv) != 2:
    print("main.py <config path>")
    exit(1)

exec(open(sys.argv[1]).read())

logging.basicConfig(format='%(asctime)s %(levelname)-8s %(name)s %(message)s', stream=sys.stdout)
logging.getLogger("bot").setLevel(logging.DEBUG)

bot = TheBot(config)
bot.run(config["token"])
bot.stop()