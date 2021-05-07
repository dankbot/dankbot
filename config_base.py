cooldown_normal = {
    "beg": 45,
    "search": 35,
    "fish": 40,
    "hunt": 40,
    "meme": 40,
    "gamble": 8,
    "blackjack": 10,
    "dep": 5,
    "withdraw": 10,
    "gift": 20,
    "give": 10,
    "steal": 30,
    "use": 5,
    "balance": 2,
    "trivia": 15,
    "buy": 5
}
cooldown_donator = {
    "beg": 30,
    "search": 25,
    "fish": 30,
    "hunt": 30,
    "meme": 30,
    "gamble": 5,
    "blackjack": 5,
    "dep": 1,
    "withdraw": 1,
    "gift": 5,
    "give": 5,
    "steal": 10,
    "use": 3,
    "balance": 1,
    "trivia": 10,
    "buy": 3
}


config = {
    # bot
    "max_reply_s": 10,
    "retry_on_timeout_s": 10,
    "search_preference": ["tree", "couch", "mailbox", "dresser", "discord", "bed", "attic", "laundromat", "grass", "shoe"],
    "modules": ["beg", "search", "give", "fish", "hunt", "pm"],
    "autodep_mode": "off",
    "autodep_threshold": (2000, 8000),
    "autodep_result": (800, 1600),

    # memer
    "bot_id": 270904126974590976,
    "bot_prefix": "pls"
}
