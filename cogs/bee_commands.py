import collections
import asyncio

import voxelbotutils as vbu
import discord
from discord.ext import commands
import asyncpg

from cogs import utils


class BeeCommands(vbu.Cog):

    @vbu.group()
    @commands.guild_only()
    async def bee(self, ctx: vbu.Context):
        """
        The parent group for the bee commands.
        """

        pass

    @bee.command(name="get")
    @vbu.defer()
    @vbu.cooldown.cooldown(1, 60 * 60, commands.BucketType.user)
    @commands.guild_only()
    async def bee_get(self, ctx: vbu.Context):
        """
        Catch some new bees for your hive.
        """

        # Get a new bee for the user
        async with self.bot.database() as db:
            drone = await utils.Bee.create_bee(db, ctx.guild.id, ctx.author.id, nobility=utils.Nobility.DRONE)
            await drone.update(db)
            princess = await utils.Bee.create_bee(db, ctx.guild.id, ctx.author.id, nobility=utils.Nobility.PRINCESS)
            await princess.update(db)

        # And respond
        return await ctx.send(
            (
                f"Created your new bees: a {drone.display_type}, **{drone.display_name}**; "
                f"and a {princess.display_type}, **{princess.display_name}**!"
            ),
            wait=False,
        )

    @bee.command(name="list")
    @vbu.defer()
    @commands.guild_only()
    async def bee_list(self, ctx: vbu.Context, user: discord.Member = None):
        """
        Shows you all of the bees you have.
        """

        # Get the bees for the given user
        user = user or ctx.author
        async with self.bot.database() as db:
            bees = await utils.Bee.fetch_bees_by_user(db, ctx.guild.id, user.id)
        if not bees:
            text = utils.format(
                "{0:pronoun,You,{1}} {0:pronoun,don't,doesn't} have any bees! :c",
                ctx.author == user,
                user.mention,
            )
            return await ctx.send(text, wait=False)

        # Collate their bees
        bee_groups = collections.defaultdict(list)
        for i in bees:
            bee_groups[i.nobility].append(i)

        # Format their bees into an embed
        description = utils.format(
            "{0:pronoun,You,{2}} {0:pronoun,have,has} **{1}** total {1:plural,bee,bees}",
            ctx.author == user,
            len(bees),
            user.mention,
        )
        embed = vbu.Embed(use_random_colour=True, description=description)
        formatter = lambda bee: f"\N{BULLET} **{bee.display_name}** ({bee.display_type})"  # noqa
        embed.add_field(
            "Queens",
            "\n".join([formatter(i) for i in bee_groups[utils.Nobility.QUEEN]]) or "None :<",
            inline=False
        )
        embed.add_field(
            "Princesses",
            "\n".join([formatter(i) for i in bee_groups[utils.Nobility.PRINCESS]]) or "None :<",
            inline=False
        )
        embed.add_field(
            "Drones",
            "\n".join([formatter(i) for i in bee_groups[utils.Nobility.DRONE]]) or "None :<",
            inline=False
        )
        return await ctx.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none(),
            wait=False,
        )

    @bee.command(name="rename")
    @vbu.defer()
    @commands.guild_only()
    async def bee_rename(self, ctx: vbu.Context, before: utils.Bee, *, after: str):
        """
        Renames one of your bees.
        """

        # Check name length
        if len(after) < 1:
            return await ctx.send("That bee name is too short!", wait=False)
        if len(after) > 50:
            return await ctx.send("That bee name is too long!", wait=False)

        # Save bee
        async with self.bot.database() as db:
            try:
                await before.update(db, name=after)
            except asyncpg.UniqueViolationError:
                return await ctx.send(
                    f"You already have a bee with the name **{after}**! >:c",
                    allowed_mentions=discord.AllowedMentions.none(),
                    wait=False,
                )
        return await ctx.send("Updated!", wait=False)

    @bee.command(name="release")
    @vbu.defer()
    @commands.guild_only()
    async def bee_release(self, ctx: vbu.Context, bee: utils.Bee = None):
        """
        Releases one of your bees back into the wild.
        """

        send_method = ctx.send

        # If they didn't give a bee then give them a dropdown
        if bee is None:
            async with self.bot.database() as db:
                bees = await utils.Bee.fetch_bees_by_user(db, ctx.guild.id, ctx.author.id)
            bees = [i for i in bees if i.hive_id is None]
            queens = [i for i in bees if i.nobility == utils.Nobility.QUEEN]
            princesses = [i for i in bees if i.nobility == utils.Nobility.PRINCESS]
            drones = [i for i in bees if i.nobility == utils.Nobility.DRONE]

            # Ask what kind of bee they want to get rid of
            components = vbu.MessageComponents.add_buttons_with_rows(
                vbu.Button("Queen", custom_id="RELEASE QUEEN", disabled=not bool(queens)),
                vbu.Button("Princess", custom_id="RELEASE PRINCESS", disabled=not bool(princesses)),
                vbu.Button("Drone", custom_id="RELEASE DRONES", disabled=not bool(drones)),
            )
            release_message = await ctx.send(
                "What kind of bee would you like to release?",
                components=components,
            )
            try:
                payload = await self.bot.wait_for("component_interaction", check=vbu.component_check(ctx.author, release_message), timeout=60)
            except asyncio.TimeoutError:
                return await ctx.send(
                    "I timed out waiting for you to say what kind of bee you want to release :<",
                    wait=False,
                )

            # Give them a dropdown to click on
            chosen_list = None
            if payload.component.custom_id == "RELEASE QUEEN":
                chosen_list = queens
            elif payload.component.custom_id == "RELEASE PRINCESS":
                chosen_list = princesses
            elif payload.component.custom_id == "RELEASE DRONES":
                chosen_list = drones
            components = vbu.MessageComponents(vbu.ActionRow(vbu.SelectMenu(
                custom_id="RELEASE SELECT",
                options=[
                    vbu.SelectOption(label=i.name, description=i.display_type, value=i.id)
                    for index, i in enumerate(chosen_list) if index < 25
                ],
                placeholder="Select all the bees that you'd like to release.",
                max_values=min(len(chosen_list), 25),
            )))
            await payload.update_message(
                content="Which bee would you like to disown?",
                components=components,
            )

            # Wait for them to select some bee IDs
            try:
                payload = await self.bot.wait_for("component_interaction", check=vbu.component_check(ctx.author, release_message), timeout=60)
            except asyncio.TimeoutError:
                return await payload.send(
                    "I timed out waiting for you to say which bees you want to release :<",
                    wait=False,
                )

            # Make the bee IDs that we want to remove
            await payload.defer_update()
            send_method = payload.message.edit
            bee_ids = payload.values

        # They specified a bee ID initially in the command
        else:
            bee_ids = [bee.id]

        # Remove all the bees
        async with self.bot.database() as db:
            await db(
                """UPDATE bees SET owner_id = NULL WHERE id = ANY($1::TEXT[])""",
                bee_ids,
            )
        return await send_method(
            content=f"Released **{bee.display_name}** into the wild \N{PENSIVE FACE}",
            components=None,
            allowed_mentions=discord.AllowedMentions.none(),
            wait=False,
        )

    @bee.command(name="pet")
    @commands.guild_only()
    async def bee_pet(self, ctx: vbu.Context, bee: utils.Bee):
        """
        Pet one of your bees on their fluffy lil heads.
        """

        return await ctx.send(
            f"**{bee.display_name}**: *Happy buzzing noises* \N{HONEYBEE}",
            allowed_mentions=discord.AllowedMentions.none(),
            wait=False,
        )

    @bee.command(name="breed")
    @vbu.defer()
    @commands.guild_only()
    async def bee_breed(self, ctx: vbu.Context):
        """
        Breed one of your princesses and drones into a queen.
        """

        # Work out what bees they have available to breed
        async with self.bot.database() as db:
            bees = await utils.Bee.fetch_bees_by_user(db, ctx.guild.id, ctx.author.id)
        princesses = {}
        drones = {}
        for bee in bees:
            if bee.hive_id:
                continue
            if bee.nobility == utils.Nobility.PRINCESS:
                princesses[bee.id] = bee
            elif bee.nobility == utils.Nobility.DRONE:
                drones[bee.id] = bee

        # See if they have any available
        if not princesses or not drones:
            return await ctx.send("You don't have an available princess and drone to breed :<", wait=False)

        # Make a check
        def get_message_check(message):
            def check(payload):
                if payload.message.id != message.id:
                    return False
                if payload.user.id != ctx.author.id:
                    self.bot.loop.create_task(payload.send(f"Only {ctx.author.mention} can interact with this select menu :<", wait=False))
                    return False
                return True
            return check

        # Ask which princess they want to breed
        components = vbu.MessageComponents(vbu.ActionRow(vbu.SelectMenu(
            custom_id="BREED BEE_SELECTION",
            options=[
                vbu.SelectOption(label=bee.name, value=bee.id, description=bee.display_type.capitalize())
                for bee in princesses.values()
            ],
            placeholder="Which princess would you like to breed?"
        )))
        dropdown_message = await ctx.send("Which of your princesses would you like to breed?", components=components)
        try:
            payload = await self.bot.wait_for("component_interaction", check=get_message_check(dropdown_message), timeout=60)
        except asyncio.TimeoutError:
            return await ctx.send("I timed out waiting for you to say which princess you want to breed :c", wait=False)
        princess = princesses[payload.values[0]]

        # Ask which drone they want to breed
        components = vbu.MessageComponents(vbu.ActionRow(vbu.SelectMenu(
            custom_id="BREED BEE_SELECTION",
            options=[
                vbu.SelectOption(label=bee.name, value=bee.id, description=bee.display_type.capitalize())
                for index, bee in enumerate(drones.values()) if index < 25
            ],
            placeholder="Which princess would you like to breed?"
        )))
        await payload.update_message(content="Which of your drones would you like to breed?", components=components)
        try:
            payload = await self.bot.wait_for("component_interaction", check=get_message_check(dropdown_message), timeout=60)
        except asyncio.TimeoutError:
            return await payload.send("I timed out waiting for you to say which drones you want to breed :c", wait=False)
        drone = drones[payload.values[0]]

        # Breed the bee
        await payload.defer_update()  # I don't think this is necessary but we'll keep it anyway
        async with self.bot.database() as db:
            try:
                new_bee = await utils.Bee.breed(db, princess, drone)
            except ValueError:
                return await payload.message.send("You can't breed anything other than a drone and a princess! :<", wait=False)

        # Tell the user about their new queen
        return await payload.message.edit(
            content=f"Your princess and drone got together and made a new {new_bee.type.value} queen, **{new_bee.display_name}**! :D",
            components=None,
            allowed_mentions=discord.AllowedMentions.none(),
            wait=False,
        )


def setup(bot: vbu.Bot):
    x = BeeCommands(bot)
    bot.add_cog(x)
