import re

P_EOL = "(?:\n|$)"
P_SHOP_ICON = "(?:.|<a?:[a-z]+:[0-9]+>)?"
P_SHOP_NAME = "[A-Za-z0-9 ]+?"
P_MENTION = "<@!?[0-9]+>"

P_MENTION_EXTRACT = re.compile("<@!?([0-9]+)>")
P_NICKNAME_SET_PING = re.compile("<@!([0-9]+)>")

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


def normalize_pings(content):
    if content is None:
        return None
    return P_NICKNAME_SET_PING.sub(lambda x: x.group(0).replace("!", ""), content)


def parse_bot_time(time):
    components = time.replace(" and ", ", ").split(", ")
    ret = 0
    for c in components:
        l, _, r = c.partition(" ")
        l = parse_bot_int(l)
        if r == "second" or r == "seconds":
            ret += l
        if r == "minute" or r == "minutes":
            ret += 60 * l
        if r == "hour" or r == "hours":
            ret += 60 * 60 * l
        if r == "day" or r == "days":
            ret += 24 * 60 * 60 * l
        if r == "month" or r == "months":
            ret += 30 * 24 * 60 * 60 * l
        if r == "year" or r == "years":
            ret += 365 * 24 * 60 * 60 * l
    return ret