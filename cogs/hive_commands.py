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
    async def hive(self, ctx: vbu.Context):
        """
        The parent command for bee hive handling.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @hive.command(name="get")
    @commands.guild_only()
    async def hive_get(self, ctx: vbu.Context):
        """
        Give yourself a new hive.
        """

        pass

    async def create_first_hive(self, ctx: vbu.Context):
        """
        Generate the first hive for a given user.
        """

        async with self.bot.database() as db:
            rows = await db(
                """INSERT INTO hives (id, index, guild_id, owner_id) VALUES
                (GEN_RANDOM_UUID(), 0, $1, $2) RETURNING *""",
                ctx.guild.id, ctx.author.id,
            )
        return utils.Hive(**rows[0])

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
            await ctx.defer()
            return await ctx.reinvoke()

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
