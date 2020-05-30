import discord
from discord.ext import commands


class MainCommandHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        return ctx.author.id == self.bot.user_id or ctx.author.id == self.bot.owner_id

    def get_user_name(self):
        return self.bot.get_user(self.bot.user_id).name

    @staticmethod
    def create_item_list(list):
        return "; ".join(f"{k}: {v}" for k, v in list)

    @staticmethod
    def parse_item_list(arr):
        items = []
        for s in arr.split(";"):
            s = s.strip()
            if s == "":
                continue
            if s[0].isdigit():
                cnt, _, what = s.partition(" ")
            elif s[-1].isdigit():
                what, _, cnt = s.rpartition(" ")
                if what.endswith(":"):
                    what = what[:-1]
            else:
                continue
            what = what.strip()
            cnt = cnt.strip()
            if what == "" or cnt == "":
                continue
            items.append((what, int(cnt)))
        return items

    @commands.command()
    async def stat(self, ctx):
        e = discord.Embed(title=self.get_user_name() + '\'s stats')
        e.add_field(name="Wallet", value=f"{self.bot.inventory.total_coins} coins")
        e.add_field(name="Grinded Coins", value=f"total: {self.bot.inventory.total_grinded}; " + self.create_item_list(self.bot.inventory.coins_stats.items()))

        inv = "; ".join(f"{k}: {v}" for k, v in self.bot.inventory.items.items())
        if inv != "":
            e.add_field(name="Inventory", value=inv)

        await ctx.send("", embed=e)

    @commands.command()
    async def gamblestat(self, ctx):
        b = self.bot.cmd.gamble_handler
        e = discord.Embed(title=self.get_user_name() + '\'s gamble stats')
        e.add_field(name="Won", value=f"{b.total_won} games, {b.total_won_money} coins")
        e.add_field(name="Lost", value=f"{b.total_lost} games, {b.total_lost_money} coins")
        e.add_field(name="Drawn", value=f"{b.total_drawn} games, {b.total_drawn_money} coins")
        await ctx.send("", embed=e)

    @commands.command()
    async def invfetch(self, ctx):
        r = await self.bot.cmd.fetch_inventory()
        await ctx.send(self.get_user_name() + "'s inventory: " + self.create_item_list(r))

    @commands.command()
    async def transfer(self, ctx, who: discord.Member, *, list):
        list = self.parse_item_list(list)
        await ctx.send("list of items to transfer: " + "; ".join(f"{k}: {v}" for [k, v] in list))
        msg = await ctx.send("i am just preparing for this...")

        for i, (what, cnt) in enumerate(list):
            await msg.edit(content=f"`({i+1}/{len(list)})  GIVE {what} {cnt}`")
            if not (await self.bot.cmd.gift(what, cnt, who.mention)).transferred:
                await ctx.send(f"failed to give {what} {cnt}")
        await msg.edit(content=f"done i think?")

    @commands.command()
    async def slowgive(self, ctx, who: discord.Member, money: int):
        max_transfer = 10000
        transfer_cnt = (money + max_transfer - 1) // max_transfer
        msg = await ctx.send(f"i am just preparing for this... ({transfer_cnt} transfers needed)")
        transfer_i = 0
        while money > 0:
            transfer_i += 1
            transfer_amount = min(money, max_transfer)
            await msg.edit(content=f"`({transfer_i}/{transfer_cnt})  GIVE {transfer_amount} ({money} remaining)`")
            if not (await self.bot.cmd.give(transfer_amount, who.mention)).transferred:
                await ctx.send(f"we failed somehow, sad and pitiful")
                break
            money -= transfer_amount
        await msg.edit(content=f"done i think?")

