from collections import defaultdict
import asyncio


class InventoryTracker:
    def __init__(self):
        self.total_coins = 0
        self.total_grinded = 0
        self.items = defaultdict(lambda: 0)
        self.coins_stats = defaultdict(lambda: 0)
        self.item_stats = defaultdict(lambda: 0)
        self.total_listeners = []

    def set_total_coins(self, coins):
        if coins == self.total_coins:
            return
        self.total_coins = coins
        for l in self.total_listeners:
            l.on_total_updated(self.total_coins)

    def add_total_coins(self, coins):
        if coins == 0:
            return
        self.total_coins += coins
        for l in self.total_listeners:
            l.on_total_updated(self.total_coins)

    def add_coins(self, count, source="unknown"):
        self.total_grinded += count
        self.coins_stats[source] += count
        self.set_total_coins(max(self.total_coins + count, 0))

    def add_item(self, item, count, source="unknown"):
        self.items[item] += count
        self.item_stats[(item, source)] += count


class TotalListener:
    def on_total_updated(self, total):
        pass


class AsyncTotalListener(TotalListener):
    def __init__(self):
        self.event = asyncio.Event()
        self.event.set()

    def on_total_updated(self, total):
        self.event.set()

    async def wait_for_update(self):
        await self.event.wait()
        self.event.clear()
