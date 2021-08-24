import collections
import asyncio

import voxelbotutils as vbu
import discord
from discord.ext import commands
import asyncpg

from cogs import utils


class BeeCommands(vbu.Cog):

    @vbu.group()
    # @commands.guild_only()
    async def bee(self, ctx: vbu.Context):
        """
        The parent group for the bee commands.
        """

        pass

    @bee.command(name="get")
    @vbu.defer()
    @vbu.cooldown.cooldown(1, 60 * 15, commands.BucketType.user)
    # @commands.guild_only()
    async def bee_get(self, ctx: vbu.Context):
        """
        Catch some new bees for your hive.
        """

        # Get a new bee for the user
        async with self.bot.database() as db:
            drone = await utils.Bee.create_bee(db, utils.get_bee_guild_id(ctx), ctx.author.id, nobility=utils.Nobility.DRONE)
            await drone.update(db)
            princess = await utils.Bee.create_bee(db, utils.get_bee_guild_id(ctx), ctx.author.id, nobility=utils.Nobility.PRINCESS)
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
    # @commands.guild_only()
    async def bee_list(self, ctx: vbu.Context, user: discord.Member = None):
        """
        Shows you all of the bees you have.
        """

        # Get the bees for the given user
        user = user or ctx.author
        async with self.bot.database() as db:
            bees = await utils.Bee.fetch_bees_by_user(db, utils.get_bee_guild_id(ctx), user.id)
        bees = [i for i in bees if i.hive_id is None]
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
        drone_types = collections.defaultdict(list)
        for i in bee_groups[utils.Nobility.DRONE]:
            drone_types[i.type].append(i)
        drone_types = list(drone_types.items())
        drone_types.sort(key=lambda item: len(item[1]), reverse=True)

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
        for t, bees in drone_types:
            embed.add_field(
                f"{t.value.title()} Drones",
                "\n".join([f"\N{BULLET} {i.display_name}" for i in bees]) or "None :<",
                inline=True
            )
        return await ctx.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none(),
            wait=False,
        )

    @bee.command(name="rename")
    @vbu.defer()
    # @commands.guild_only()
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
    # @commands.guild_only()
    async def bee_release(self, ctx: vbu.Context, *, bee: utils.Bee = None):
        """
        Releases one of your bees back into the wild.
        """

        send_method = ctx.send

        # If they didn't give a bee then give them a dropdown
        if bee is None:
            async with self.bot.database() as db:
                bees = await utils.Bee.fetch_bees_by_user(db, utils.get_bee_guild_id(ctx), ctx.author.id)
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
            content=utils.format("Released **{0}** {0:plural,bee,bees} into the wild \N{PENSIVE FACE}", len(bee_ids)),
            components=None,
            allowed_mentions=discord.AllowedMentions.none(),
            wait=False,
        )

    @bee.command(name="pet")
    # @commands.guild_only()
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
    # @commands.guild_only()
    async def bee_breed(self, ctx: vbu.Context):
        """
        Breed one of your princesses and drones into a queen.
        """

        # Work out what bees they have available to breed
        async with self.bot.database() as db:
            bees = await utils.Bee.fetch_bees_by_user(db, utils.get_bee_guild_id(ctx), ctx.author.id)
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
        if not princesses:
            return await ctx.send("You don't have an available princess to breed :<", wait=False)
        if not drones:
            return await ctx.send("You don't have an available drone to breed :<", wait=False)

        # Ask which princess they want to breed
        components = vbu.MessageComponents(
            vbu.ActionRow(vbu.SelectMenu(
                custom_id="BREED BEE_SELECTION",
                options=[
                    vbu.SelectOption(label=bee.name, value=bee.id, description=bee.display_type.capitalize())
                    for bee in princesses.values()
                ],
                placeholder="Which princess would you like to breed?"
            )),
            vbu.ActionRow(vbu.Button(
                label="Cancel",
                custom_id="BREED CANCEL",
                style=vbu.ButtonStyle.DANGER,
            )),
        )
        dropdown_message = await ctx.send("Which of your princesses would you like to breed?", components=components)
        try:
            payload = await self.bot.wait_for("component_interaction", check=vbu.component_check(ctx.author, dropdown_message), timeout=60)
        except asyncio.TimeoutError:
            return await ctx.send("I timed out waiting for you to say which princess you want to breed :c", wait=False)
        if payload.component.custom_id == "BREED CANCEL":
            return await payload.update_message(content="Cancelled your bee breed :<", components=None)
        princess = princesses[payload.values[0]]

        # Ask which drone they want to breed
        components = vbu.MessageComponents(
            vbu.ActionRow(vbu.SelectMenu(
                custom_id="BREED BEE_SELECTION",
                options=[
                    vbu.SelectOption(label=i.title(), value=i)
                    for i in set([o.type.value for o in drones.values()])
                ],
                placeholder="What type of drone would you like to breed?"
            )),
            vbu.ActionRow(vbu.Button(
                label="Cancel",
                custom_id="BREED CANCEL",
                style=vbu.ButtonStyle.DANGER,
            )),
        )
        await payload.update_message(content="What type of drone would you like to breed?", components=components)
        try:
            payload = await self.bot.wait_for("component_interaction", check=vbu.component_check(ctx.author, dropdown_message), timeout=60)
        except asyncio.TimeoutError:
            return await payload.send("I timed out waiting for you to say which drones you want to breed :c", wait=False)
        if payload.component.custom_id == "BREED CANCEL":
            return await payload.update_message(content="Cancelled your bee breed :<", components=None)
        drone_type = payload.values[0]

        # Ask which drone they want to breed
        components = vbu.MessageComponents(
            vbu.ActionRow(vbu.SelectMenu(
                custom_id="BREED BEE_SELECTION",
                options=[
                    vbu.SelectOption(label=bee.name, value=bee.id, description=bee.display_type.capitalize())
                    for bee in [o for o in drones.values() if o.type.value == drone_type][:25]
                ],
                placeholder="Which drone would you like to breed?"
            )),
            vbu.ActionRow(vbu.Button(
                label="Cancel",
                custom_id="BREED CANCEL",
                style=vbu.ButtonStyle.DANGER,
            )),
        )
        await payload.update_message(content="Which of your drones would you like to breed?", components=components)
        try:
            payload = await self.bot.wait_for("component_interaction", check=vbu.component_check(ctx.author, dropdown_message), timeout=60)
        except asyncio.TimeoutError:
            return await payload.send("I timed out waiting for you to say which drones you want to breed :c", wait=False)
        if payload.component.custom_id == "BREED CANCEL":
            return await payload.update_message(content="Cancelled your bee breed :<", components=None)
        drone = drones[payload.values[0]]

        # Breed the bee
        await payload.defer_update()  # I don't think this is necessary but we'll keep it anyway
        async with self.bot.database() as db:
            try:
                new_bee = await utils.Bee.breed(db, princess, drone)
            except ValueError:
                return await payload.message.send("You can't breed anything other than a drone and a princess! :<", wait=False)

            # Store our cross-bred types
            await db(
                """INSERT INTO user_bee_combinations (guild_id, user_id, left_type, right_type, result_type)
                VALUES ($1, $2, $3, $4, $5)""",
                utils.get_bee_guild_id(ctx), ctx.author.id, *sorted([princess.type.value, drone.type.value]),
                new_bee.type.value,
            )

        # Tell the user about their new queen
        return await payload.message.edit(
            content=f"Your princess and drone got together and made a new {new_bee.type.value} queen, **{new_bee.display_name}**! :D",
            components=None,
            allowed_mentions=discord.AllowedMentions.none(),
            wait=False,
        )

    @bee.command(name="map")
    @vbu.defer()
    async def bee_map(self, ctx: vbu.Context):
        """
        Map out the bee combinations that you've discovered.
        """

        # Grab their bee combinations
        async with self.bot.database() as db:
            bee_rows = await db(
                """SELECT * FROM user_bee_combinations WHERE guild_id = $1 AND user_id = $2""",
                utils.get_bee_guild_id(ctx), ctx.author.id,
            )

        # Generate some dot lines that we can use
        output = []
        output.append("rankdir=LR;")
        for row in bee_rows:
            left = utils.BeeType.get(row['left_type'])
            right = utils.BeeType.get(row['right_type'])
            result = utils.BeeType.get(row['result_type'])
            joiner = f"{left}{right}"
            if left.is_mundane:
                v = f"\"{left.value.title()} Bee\" [color=red];"
                if v not in output:
                    output.append(v)
            if right.is_mundane:
                v = f"\"{right.value.title()} Bee\" [color=red];"
                if v not in output:
                    output.append(v)
            output.append((
                f"\"{joiner}\" [label=\"\",height=0.001,width=0.001];"
                f"\"{left.value.title()} Bee\" -> \"{joiner}\" [dir=none];"
                f"\"{right.value.title()} Bee\" -> \"{joiner}\" [dir=none];"
                f"{joiner} -> \"{result.value.title()} Bee\";"
            ))

        # See if we have an output
        if not output:
            return await ctx.send("You've not cross-bred any bees yet :<")

        # Write the dot to a file
        dot_filename = f'./.{ctx.author.id}.gz'
        try:
            output_string = "".join(output)
            with open(dot_filename, 'w', encoding='utf-8') as a:
                a.write(f"digraph {{ {output_string} }}")
        except Exception as e:
            self.logger.error(f"Could not write to {dot_filename}")
            raise e

        # Convert to an image
        image_filename = f'./.{ctx.author.id}.png'
        format_rendering_option = '-Tpng:cairo'
        dot = await asyncio.create_subprocess_exec('dot', format_rendering_option, dot_filename, '-o', image_filename, '-Gcharset=UTF-8')
        await asyncio.wait_for(dot.wait(), 10.0)

        # Kill subprocess
        try:
            dot.kill()
        except ProcessLookupError:
            pass  # It already died
        except Exception:
            raise

        # Send file
        try:
            file = discord.File(image_filename)
        except FileNotFoundError:
            return await ctx.send("I was unable to send your bee map image - please try again later.")
        await ctx.send(file=file)
        await asyncio.sleep(1)

        # Delete the files
        self.bot.loop.create_task(asyncio.create_subprocess_exec('rm', dot_filename))
        self.bot.loop.create_task(asyncio.create_subprocess_exec('rm', image_filename))


def setup(bot: vbu.Bot):
    x = BeeCommands(bot)
    bot.add_cog(x)
