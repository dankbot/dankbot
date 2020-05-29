import re

P_EOL = "(?:\n|$)"
P_SHOP_ICON = "(?:.|<a?:[a-z]+:[0-9]+>)?"
P_SHOP_NAME = "[A-Za-z0-9 ]+?"
P_MENTION = "<@!?[0-9]+>"

P_MENTION_EXTRACT = re.compile("<@!?([0-9]+)>")

P_NON_ASCII = re.compile("[^\x20-\x7e]")

P_HINT = re.compile("(?:\n\n|^)\\*\\*Handy Dandy Tip\\*\\*: .*$")


def get_mention_user_id(txt):
    r = P_MENTION_EXTRACT.match(txt)
    if r:
        return int(r.group(1))
    return None


def filter_ascii(txt):
    return P_NON_ASCII.sub("", txt)


def parse_bot_int(i):
    return int(i.replace(",", ""))


def filter_out_hint(content):
    return P_HINT.sub("", content)
