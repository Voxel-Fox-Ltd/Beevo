import asyncio
import enum

import voxelbotutils as vbu
import discord
from discord.ext import commands

from cogs import utils


HiveShow = enum.Enum("HiveInclude", "all bees items")


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
            comb_rows = await db(
                """
                SELECT
                    hive_id,
                    type,
                    FLOOR(RANDOM() * (FLOOR(CAST(bees.speed AS REAL) / 100) + 1) + 1) quantity
                FROM
                    bees
                WHERE
                    hive_id IS NOT NULL
                    AND nobility = 'Queen'
                    AND lived_lifetime < lifetime
                    AND RANDOM() * 100 <= speed
                """
            )
            comb_adds = [
                (row['hive_id'], utils.BeeType.get(row['type']).get_comb(), row['quantity'],)
                for row in comb_rows
            ]
            await db.execute_many(
                """
                INSERT INTO
                    hive_inventory
                    (hive_id, item_name, quantity)
                VALUES
                    ($1, INITCAP($2 || ' Comb'), $3)
                ON CONFLICT
                    (hive_id, item_name)
                DO UPDATE SET
                    quantity = hive_inventory.quantity + excluded.quantity
                """,
                *comb_adds,
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
            dead_queen_list = [utils.Bee(**i) for i in dead_queen_rows]
            dead_queens = {i.hive_id: i for i in dead_queen_list}
            queen_death_tasks = [i.die(db) for i in dead_queens.values()]
            new_bees = await asyncio.gather(*queen_death_tasks)

            # Get the owner IDs for every bee that's died
            results = []
            for i in new_bees:
                try:
                    results.extend(i)
                except Exception as e:
                    self.logger.error(e, exc_info=e)
            all_owner_ids = {i.hive: i.owner_id for i in results}

            # DM authors who want to know when the bees die
            for hive, owner_id in all_owner_ids.items():
                try:
                    owner = self.bot.get_user(owner_id) or await self.bot.fetch_user(owner_id)
                    try:
                        text = f"**{dead_queens[hive.id].display_name}** in hive **{hive.name}** has perished :<",
                    except KeyError:
                        text = f"Your queen in hive **{hive.name}** has perished :<",
                    await owner.send(
                        content=text,
                        components=vbu.MessageComponents(vbu.ActionRow(
                            vbu.Button("See your hives", custom_id="RUNCOMMAND hive list", style=vbu.ButtonStyle.SECONDARY),
                        )),
                    )
                except discord.HTTPException:
                    pass

    @vbu.group(invoke_without_command=False)
    async def hive(self, ctx: vbu.Context):
        """
        The parent command for bee hive handling.
        """

        if ctx.invoked_subcommand is None:
            return await ctx.send_help(ctx.command)

    @hive.command(name="list")
    @vbu.defer()
    async def hive_list(self, ctx: vbu.Context, user: discord.Member = None):
        """
        Give you a list of all of your hives.
        """

        # Grab their hives
        user = user or ctx.author
        async with self.bot.database() as db:
            hives = await utils.Hive.fetch_hives_by_user(db, utils.get_bee_guild_id(ctx), user.id)

        # Make our content
        content = utils.format(
            "{0:pronoun,You,{2}} {0:pronoun,have,has} **{1}** {1:plural,hive,hives}:",
            ctx.author == user,
            len(hives),
            user.mention,
        )
        embeds = []

        # We have data for each hive
        hive_queen_count = 0
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
                        hive_queen_count += 1
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
            if item_field_value:
                embed.add_field(
                    "Inventory",
                    item_field_value,
                    inline=False,
                )

            # We're done with this embed
            embeds.append(embed)

        # And send
        components = None
        if hive_queen_count != len(hives):
            components = vbu.MessageComponents(vbu.ActionRow(
                vbu.Button("Clear your hives", custom_id="RUNCOMMAND hive clear", style=vbu.ButtonStyle.SECONDARY),
            ))
        return await ctx.send(
            content,
            embeds=embeds,
            components=components,
        )

    @hive.command(name="add")
    @vbu.defer()
    async def hive_add(self, ctx: vbu.Context, bee: utils.Bee = None, hive: utils.Hive = None):
        """
        Add one of your queens to a hive.
        """

        # Set up our sendable
        send_method = ctx.send
        dropdown_message = None

        # See that they gave a bee
        if bee is None:
            payload, dropdown_message, bee = await utils.Bee.send_bee_dropdown(
                ctx=ctx, send_method=send_method, current_message=dropdown_message,
                group_by_type=True, check=lambda bee: bee.nobility == utils.Nobility.QUEEN,
            )
            if not bee:
                return
            else:
                bee = bee[0]
            if payload:
                send_method = payload.update_message

        # See that they gave a hive
        if hive is None:
            payload, dropdown_message, hive = await utils.Hive.send_hive_dropdown(
                ctx=ctx, send_method=send_method, current_message=dropdown_message,
                check=lambda hive: not [i for i in hive.bees if i.nobility == utils.Nobility.QUEEN],
            )
            if not hive:
                return
            else:
                hive = hive[0]
            if payload:
                send_method = payload.update_message

        # See if the bee is already in a hive
        if bee.hive_id:
            return await send_method(
                content=f"**{bee.name}** is already in **{hive.name}**!",
                allowed_mentions=discord.AllowedMentions.none(),
                components=None,
            )

        # See if the hive already has a bee
        if [i for i in hive.bees if i.nobility == utils.Nobility.QUEEN]:
            return await send_method(
                content=f"There's already a bee in **{hive.name}**!",
                components=None,
            )

        # Actually move the bee around
        async with ctx.typing():
            async with self.bot.database() as db:
                await bee.update(db, hive_id=hive.id)

        # And done!
        return await send_method(
            content=f"**{bee.name}** buzzes on happily and flys into **{hive.name}* :>",
            allowed_mentions=discord.AllowedMentions.none(),
            components=vbu.MessageComponents(vbu.ActionRow(
                vbu.Button("View your hive", custom_id="RUNCOMMAND hive list", style=vbu.ButtonStyle.SECONDARY),
            )),
        )

    @hive.command(name="clear")
    @vbu.defer()
    async def hive_clear(self, ctx: vbu.Context, *, hive: utils.Hive = None):
        """
        Clear out the bees from one of your hives.
        """

        # Set up the send method
        send_method = ctx.send
        current_message = None

        # Make sure they give a hive
        if hive is None:
            payload, current_message, hive = await utils.Hive.send_hive_dropdown(
                ctx=ctx, send_method=send_method, current_message=None,
                check=lambda hive: hive.bees or hive.inventory,
            )
            if not hive:
                return
            else:
                hive = hive[0]
            if payload:
                send_method = payload.update_message

        # See if the hive has a bee
        if not hive.bees and hive.inventory.is_empty():
            return await send_method(
                content=f"There's nothing in **{hive.name}** :<",
                components=None,
            )

        # See if the hive has a queen in it
        hive_queens = [i for i in hive.bees if i.nobility == utils.Nobility.QUEEN]
        if hive_queens:
            current_message = await send_method(
                content=f"Are you sure? There's an active queen in **{hive.name}** :<",
                components=vbu.MessageComponents.boolean_buttons(),
            ) or current_message
            try:
                payload = await self.bot.wait_for("component_interaction", check=vbu.component_check(ctx.author, current_message), timeout=60)
            except asyncio.TimeoutError:
                return await current_message.edit(content="Timed out waiting for you to confirm hive clear :<", components=None)
            if payload.component.custom_id == "NO":
                return await payload.update_message(content="Alright, cancelling you hive clear!", components=None)
            current_message = payload.message
            send_method = payload.update_message

        # Alright move the bee
        bee_count = len(hive.bees)
        async with ctx.typing():
            async with self.bot.database() as db:
                await db("""UPDATE bees SET hive_id = NULL WHERE hive_id = $1""", hive.id)
                await db.start_transaction()
                await db(
                    """
                    INSERT INTO
                        user_inventory (guild_id, user_id, item_name, quantity)
                    SELECT
                        $1, $2, item_name, quantity
                    FROM
                        hive_inventory
                    WHERE
                        hive_id = $3
                    ON CONFLICT
                        (guild_id, user_id, item_name)
                    DO UPDATE SET
                        quantity = user_inventory.quantity + excluded.quantity
                    """,
                    utils.get_bee_guild_id(ctx), ctx.author.id, hive.id,
                )
                await db("""UPDATE hive_inventory SET quantity = 0 WHERE hive_id = $1""", hive.id)
                await db.commit_transaction()

        # And done
        item_names = []
        if bee_count:
            item_names.append(utils.format("{0} {0:plural,bee,bees}", bee_count))
        for item in hive.inventory.values():
            if item.quantity:
                item_names.append(utils.format("{0.quantity} {0.quantity:plural,{1},{1}s}", item, item.name.lower()))
        item_names = [f"**{i}**" for i in item_names]
        return await send_method(
            content=utils.format("Moved {0:humanjoin} out of **{1.name}**~", item_names, hive),
            components=None,
        )


def setup(bot: vbu.Bot):
    x = HiveCommands(bot)
    bot.add_cog(x)
