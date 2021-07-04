from discord.ext import commands
import voxelbotutils as vbu

from cogs import utils


class BeeCommands(vbu.Cog):

    @vbu.command()
    @commands.guild_only()
    async def testbee(self, ctx: vbu.Context):
        """
        Generate a test bee for you to flirt with.
        """

        async with self.bot.database() as db:
            bee = await utils.Bee.create_bee(db, ctx.author.id)
        return await ctx.send(f"Created your bee! `{bee.id}`")


def setup(bot: vbu.Bot):
    x = BeeCommands(bot)
    bot.add_cog(x)
