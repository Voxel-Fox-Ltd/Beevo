import asyncio

import voxelbotutils as vbu
import discord
from discord.ext import commands

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

            # Add some honey combs
            await db(
                """
                INSERT INTO
                    hive_inventory
                    (hive_id, item_name, quantity)
                SELECT
                    bees.hive_id,
                    INITCAP(bee_comb_type.comb || ' Comb'),
                    FLOOR(RANDOM() * (FLOOR(CAST(bees.speed AS REAL) / 100) + 1) + 1)
                FROM
                    bees
                LEFT JOIN
                    bee_comb_type
                ON
                    bees.type = bee_comb_type.type
                WHERE
                    hive_id IS NOT NULL
                    AND nobility = 'Queen'
                    AND lived_lifetime < lifetime
                    AND RANDOM() * 100 <= speed
                ON CONFLICT
                    (hive_id, item_name)
                DO UPDATE SET
                    quantity = hive_inventory.quantity + excluded.quantity
                """
            )

            # See which of the bees are dead
            dead_queen_rows = await db(
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
            dead_queens = [utils.Bee(**i) for i in dead_queen_rows]
            queen_death_tasks = [i.die(db) for i in dead_queens]
            await asyncio.gather(*queen_death_tasks)

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

        # Make our content
        content = utils.format(
            "{0:pronoun,You,{2}} {0:pronoun,have,has} **{1}** {1:plural,hive,hives}:",
            ctx.author == user,
            len(hives),
            user.mention,
        )
        embed = vbu.Embed(use_random_colour=True, description="")
        embeds = []

        # We have data for each hive
        for h in hives:
            embed = vbu.Embed(use_random_colour=True, title=h.name, description=h.get_hive_grid())
            bee_field_value = ""
            bee_is_queen = False
            item_field_value = ""

            # If the hive has bees
            if h.bees:
                for i in h.bees:
                    if i.nobility == utils.Nobility.QUEEN:
                        bee_is_queen = True
                        line = (
                            f"**{i.name}** (*{i.display_type}*)\n"
                            f"{{:progress,9}}"
                        )
                        bee_field_value += utils.format(line, ((i.lifetime - i.lived_lifetime) * 100) / i.lifetime)
                    else:
                        bee_field_value += f"\n\N{BULLET} {i.name} ({i.display_type})"

            # If the hive has an inventory
            if h.inventory:
                for i in h.inventory.values():
                    if i.quantity > 0:
                        line = f"\n\N{BULLET} {i.name} x{i.quantity}"
                        item_field_value += line

            # Add fields
            if bee_field_value:
                embed.add_field(
                    "Active Bees" if bee_is_queen else "Bees",
                    bee_field_value,
                    inline=False,
                )
            else:
                embed.add_field(
                    "Bees",
                    "Empty :<",
                    inline=False,
                )
            if item_field_value:
                embed.add_field(
                    "Inventory",
                    item_field_value,
                    inline=False,
                )

            # We're done with this embed
            embeds.append(embed)

        # And send
        return await ctx.send(content, embeds=embeds, wait=False)

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
                await db("""UPDATE bees SET hive_id = NULL WHERE hive_id = $1""", hive.id)
                await db.start_transaction()
                await db(
                    """
                    INSERT INTO
                        user_inventory (user_id, item_name, quantity)
                    SELECT
                        $1, item_name, quantity
                    FROM
                        hive_inventory
                    WHERE
                        hive_id = $2
                    ON CONFLICT
                        (user_id, item_name)
                    DO UPDATE SET
                        quantity = user_inventory.quantity + excluded.quantity
                    """,
                    ctx.author.id, hive.id,
                )
                await db("""UPDATE hive_inventory SET quantity = 0 WHERE hive_id = $1""", hive.id)
                await db.commit_transaction()

        # And done
        return await ctx.send(
            f"Moved **{bee_count}** bee{'s' if bee_count > 1 else ''} out of **{hive.name}**~",
            wait=False,
        )


def setup(bot: vbu.Bot):
    x = HiveCommands(bot)
    bot.add_cog(x)
