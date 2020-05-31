from discord.ext import commands


class WrapperCommandHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        return ctx.author.id == self.bot.user_id or ctx.author.id == self.bot.owner_id

    @commands.command()
    async def beg(self, ctx):
        r = await self.bot.cmd.beg()
        await ctx.send(str(r))

    @commands.command()
    async def search(self, ctx):
        r = await self.bot.cmd.search_with_preferences()
        await ctx.send(str(r))

    @commands.command()
    async def fish(self, ctx):
        r = await self.bot.cmd.fish()
        await ctx.send(str(r))

    @commands.command()
    async def hunt(self, ctx):
        r = await self.bot.cmd.hunt()
        await ctx.send(str(r))

    @commands.command()
    async def pm(self, ctx):
        r = await self.bot.cmd.post_meme()
        await ctx.send(str(r))

    @commands.command()
    async def dep(self, ctx, amount: int):
        r = await self.bot.cmd.deposit(amount)
        await ctx.send(str(r))

    @commands.command()
    async def withdraw(self, ctx, amount: int):
        r = await self.bot.cmd.withdraw(amount)
        await ctx.send(str(r))

    @commands.command()
    async def bal(self, ctx):
        r = await self.bot.cmd.balance()
        await ctx.send(str(r))

    @commands.command()
    async def gamble(self, ctx, amount: int):
        r = await self.bot.cmd.gamble(amount)
        await ctx.send(str(r))

    @commands.command()
    async def trivia(self, ctx):
        r = await self.bot.cmd.trivia()
        await ctx.send(str(r))

    @commands.command()
    async def buy(self, ctx, what, amount: int):
        r = await self.bot.cmd.buy(what, amount)
        await ctx.send(str(r))

    @commands.command()
    async def blackjack(self, ctx, amount: int):
        r = await self.bot.cmd.blackjack(amount)
        await ctx.send(str(r))
