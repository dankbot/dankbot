import re


class MemeBot:
    P_NO_LAPTOP = re.compile("^oi you need to buy a laptop in the shop to post memes$")
    P_REPLY_OK = re.compile("^Your meme got \\*\\*[0-9,]+ upvotes\\*\\*. You get ([0-9,]+) coins from the ads$")
    P_REPLY_TRENDING1 = re.compile(f"^Your meme is \\*\\*__TRENDING__\\*\\* with \\*\\*[0-9,]+\\*\\*. You get ([0-9,]+) coins, also a fan of your memes sent you ([0-9,]+) {P_SHOP_ICON} \\*\\*({P_SHOP_NAME})\\*\\*$")
