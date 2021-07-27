import voxelbotutils as vbu
from discord.ext import commands, tasks

from cogs import utils


class HiveCommands(vbu.Cog):

    @tasks.loop(seconds=1)
    async def hive_lifetime_ticker(self):
        """
        Tick every second to run a lifetime for the bees.
        """

        pass

    @vbu.group(invoke_without_command=False)
    @commands.guild_only()
    async def hive(self, ctx: vbu.Context, *, hive: utils.Hive):
        """
        The parent command for bee hive handling.
        """

        pass

    @hive.command(name="get")
    @commands.guild_only()
    async def hive_get(self, ctx: vbu.Context):
        """
        Give yourself a new hive.
        """

        pass

    @hive.command(name="list")
    @commands.guild_only()
    async def hive_list(self, ctx: vbu.Context):
        """
        Give you a list of all of your hives.
        """

        # Grab their hives
        async with self.bot.database() as db:
            rows = await db(
                """SELECT * FROM hives WHERE guild_id=$1 AND owner_id=$2""",
                ctx.guild.id, ctx.author.id,
            )
        if not rows:
            return await ctx.send("You don't have any hives yet! :<", wait=False)

        # Format into an embed
        embed = vbu.Embed(use_random_colour=True, description="")
        for r in rows:
            embed.description += f"\n\N{BULLET} {r['name']}"
        return await ctx.send(embed=embed, wait=False)

    @hive.command(name="add")
    @commands.guild_only()
    async def hive_add(self, ctx: vbu.Context, bee: utils.Bee):
        """
        Add one of your bees to a hive.
        """

        pass

    @hive.command(name="remove")
    @commands.guild_only()
    async def hive_remove(self, ctx: vbu.Context, hive: utils.Hive, bee: utils.Bee):
        """
        Remove one of your bees from a hive.
        """

        pass


def setup(bot: vbu.Bot):
    x = HiveCommands(bot)
    bot.add_cog(x)
