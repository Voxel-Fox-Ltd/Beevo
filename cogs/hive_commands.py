import asyncio

import voxelbotutils as vbu
import discord
from discord.ext import commands, tasks

from cogs import utils


class HiveCommands(vbu.Cog):

    @vbu.Cog.listener("on_bee_tick")
    async def hive_lifetime_ticker(self):
        """
        Update the bees' lived lifetime every tick.
        """

        # Open the database
        async with self.bot.database() as db:

            # Update bee lifetimes
            await db(
                """
                UPDATE
                    bees
                SET
                    lived_lifetime = lived_lifetime + 1
                WHERE
                    hive_id IS NOT NULL -- is in a hive
                    AND nobility = 'Queen'  -- is a queen
                    AND lived_lifetime < lifetime  -- hasn't lived its life
                """,
            )

            # See which of the bees are dead
            dead_bee_rows = await db(
                """
                SELECT
                    *
                FROM
                    bees
                WHERE
                    hive_id IS NOT NULL
                    AND nobility = 'Queen'
                    AND lived_lifetime >= lifetime
                """
            )

            # And handle those heckos
            dead_bees = [utils.Bee(**i) for i in dead_bee_rows]
            bee_death_tasks = [i.die(db) for i in dead_bees]
            await asyncio.gather(bee_death_tasks)

    @vbu.group(invoke_without_command=False)
    @commands.guild_only()
    async def hive(self, ctx: vbu.Context):
        """
        The parent command for bee hive handling.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    async def create_first_hive(self, guild_id: int, user_id: int):
        """
        Generate the first hive for a given user.
        """

        async with self.bot.database() as db:
            rows = await db(
                """INSERT INTO hives (id, index, guild_id, owner_id) VALUES
                (GEN_RANDOM_UUID(), 0, $1, $2) RETURNING *""",
                guild_id, user_id,
            )
        return utils.Hive(**rows[0])

    @hive.command(name="list")
    @vbu.defer()
    @commands.guild_only()
    async def hive_list(self, ctx: vbu.Context, user: discord.Member = None):
        """
        Give you a list of all of your hives.
        """

        # Grab their hives
        user = user or ctx.author
        async with self.bot.database() as db:
            hives = await utils.Hive.fetch_hives_by_user(db, ctx.guild.id, user.id)
        if not hives:
            await self.create_first_hive(ctx.guild.id, user.id)
            return await ctx.reinvoke()

        # Format into an embed
        description = utils.format(
            "{0:pronoun,You,{2}} {0:pronoun,have,has} **{1}** {1:plural,hive,hives}:",
            ctx.author == user,
            len(hives),
            user.mention,
        )
        embed = vbu.Embed(use_random_colour=True, description=description)
        for h in hives:
            if h.bees:
                embed.description += f"\n\N{BULLET} **{h.name}**"
                for i in h.bees:
                    embed.description += f"\n\u2800\u2800\N{BULLET} {i.name}"
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

    @hive.command(name="clear")
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
