import voxelbotutils as vbu
import discord
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

    # @hive.command(name="get")
    # @commands.guild_only()
    # async def hive_get(self, ctx: vbu.Context):
    #     """
    #     Give yourself a new hive.
    #     """

    #     pass

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
    @vbu.defer()
    @commands.guild_only()
    async def hive_list(self, ctx: vbu.Context):
        """
        Give you a list of all of your hives.
        """

        # Grab their hives
        async with self.bot.database() as db:
            hives = await utils.Hive.fetch_hives_by_user(db, ctx.guild.id, ctx.author.id)
        if not hives:
            await self.create_first_hive(ctx)
            return await ctx.reinvoke()

        # Format into an embed
        embed = vbu.Embed(use_random_colour=True, description=f"You have **{len(hives)}** hive{'s' if len(hives) > 1 else ''}:")
        for h in hives:
            if h.bees:
                embed.description += f"\n\N{BULLET} **{h.name}**"
                for i in h.bees:
                    embed.description += f"\n\u200b    \N{BULLET} {i.name}"
            else:
                embed.description += f"\n\N{BULLET} **{h.name}** (*empty*)"
        return await ctx.send(embed=embed, wait=False)

    @hive.command(name="add")
    @vbu.defer()
    @commands.guild_only()
    async def hive_add(self, ctx: vbu.Context, bee: utils.Bee, hive: utils.Hive):
        """
        Add one of your queens to a hive.
        """

        # See if the bee is already in a hive
        if bee.hive_id:
            return await ctx.send(
                f"**{bee.name}** is already in **{hive.name}**!",
                allowed_mentions=discord.AllowedMentions.none(),
                wait=False,
            )

        # See if the hive already has a bee
        if hive.bees:
            return await ctx.send(
                f"There's already a bee in **{hive.name}**!",
                wait=False,
            )

        # Actually move the bee around
        async with ctx.typing():
            async with self.bot.database() as db:
                await bee.update(db, hive_id=hive.id)

        # And done!
        return await ctx.send(
            f"Successfully moved **{bee.name}** into **{hive.name}**!",
            allowed_mentions=discord.AllowedMentions.none(),
            wait=False,
        )

    @hive.command(name="remove")
    @vbu.defer()
    @commands.guild_only()
    async def hive_clear(self, ctx: vbu.Context, hive: utils.Hive):
        """
        Clear out the bees from one of your hives.
        """

        # See if the hive has a bee
        if not hive.bees:
            return await ctx.send(
                f"There's no bee in **{hive.name}** :<",
                wait=False,
            )

        # Alright move the bee
        bee_count = len(hive.bees)
        async with ctx.typing():
            async with self.bot.database() as db:
                for bee in hive.bees:
                    await bee.update(db, hive_id=None)

        # And done
        return await ctx.send(
            f"Moved **{bee_count}** bee{'s' if bee_count > 1 else ''} out of **{hive.name}**~",
            wait=False,
        )


def setup(bot: vbu.Bot):
    x = HiveCommands(bot)
    bot.add_cog(x)
