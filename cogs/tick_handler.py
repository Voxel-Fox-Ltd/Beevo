import voxelbotutils as vbu
from discord.ext import tasks


class TickHandler(vbu.Cog):

    def __init__(self, bot: vbu.Bot):
        super().__init__(bot)
        self.ticker.start()

    def cog_unload(self):
        self.ticker.stop()

    @tasks.loop(seconds=5)  # 1 tick is 5 seconds
    async def ticker(self):
        self.bot.dispatch("bee_tick")

    @ticker.before_loop
    async def before_ticker(self):
        await self.bot.wait_until_ready()


def setup(bot: vbu.Bot):
    x = TickHandler(bot)
    bot.add_cog(x)
