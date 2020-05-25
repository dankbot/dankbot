from collections import defaultdict


class InventoryTracker:
    def __init__(self):
        self.total_coins = 0
        self.items = defaultdict(lambda: 0)
        self.coins_stats = defaultdict(lambda: 0)
        self.item_stats = defaultdict(lambda: 0)

    def add_coins(self, count, source="unknown"):
        self.total_coins += count
        self.coins_stats[source] += count

    def add_item(self, item, count, source="unknown"):
        self.items[item] += count
        self.item_stats[(item, source)] += count
