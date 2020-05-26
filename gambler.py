class TheGambler:
    def __init__(self, bot):
        self.gamble_amount_base = bot.config["gamble_base"]
        self.gamble_amount = 0

    def set_base(self, base):
        self.gamble_amount_base = base

    def on_gamble_start(self):
        if self.gamble_amount < self.gamble_amount_base:
            self.gamble_amount = self.gamble_amount_base
        return self.gamble_amount

    def on_gamble_complete(self, amount):
        self.gamble_amount -= amount
        if self.gamble_amount <= 0:
            self.gamble_amount = 0
