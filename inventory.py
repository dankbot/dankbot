from collections import defaultdict


class InventoryTracker:
    def __init__(self):
        self.total_coins = 0
        self.total_grinded = 0
        self.items = defaultdict(lambda: 0)
        self.coins_stats = defaultdict(lambda: 0)
        self.item_stats = defaultdict(lambda: 0)
        self.listeners = []

    def set_total_coins(self, coins):
        self.total_coins = coins

    def add_total_coins(self, coins):
        self.total_coins += coins

    def add_coins(self, count, source="unknown"):
        self.total_coins = max(self.total_coins + count, 0)
        self.total_grinded += count
        self.coins_stats[source] += count
        for l in self.listeners:
            l.on_coins_added(count, source)

    def add_item(self, item, count, source="unknown"):
        self.items[item] += count
        self.item_stats[(item, source)] += count
        for l in self.listeners:
            l.on_item_added(item, count, source)


class InventoryTrackerListener:
    def on_coins_added(self, count, source):
        pass

    def on_item_added(self, item, count, source):
        pass