import collections
import asyncio

import voxelbotutils as vbu
import discord
from discord.ext import commands
import asyncpg

from cogs import utils


class BeeCommands(vbu.Cog):

    @vbu.group()
    async def bee(self, ctx: vbu.Context):
        """
        The parent group for the bee commands.
        """

        pass

    @bee.command(name="get")
    @vbu.defer()
    @vbu.cooldown.cooldown(1, 60 * 15, commands.BucketType.user)
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
            components=vbu.MessageComponents(vbu.ActionRow(
                vbu.Button("Breed your bees", custom_id="RUNCOMMAND bee breed", style=vbu.ButtonStyle.SECONDARY),
            )),
        )

    @bee.command(name="analyze", aliases=["analyse"])
    @vbu.defer()
    @commands.is_owner()
    async def bee_analyze(self, ctx: vbu.Context, bee: utils.Bee = None):
        """
        Give you the stats for one of your bees.
        """

        # Set the send method
        send_method = ctx.send

        # See if they gave a bee
        if not bee:
            payload, _, bee = await utils.Bee.send_bee_dropdown(
                ctx=ctx, send_method=send_method, current_message=None,
                group_by_nobility=True, group_by_type=True,
            )
            if not bee:
                return
            else:
                bee = bee[0]
            if payload:
                send_method = payload.update_message

        # Work out the stats
        embed = vbu.Embed(use_random_colour=True, title=f"{bee.name}; {bee.display_type}")
        embed.description = (
            f"**Speed**: {bee.speed}\n"
            f"**Fertility**: {bee.fertility}\n"
            f"**Lifetime**: {bee.lifetime}\n"
        )

        # And respond
        return await send_method(
            content=None,
            embed=embed,
            components=None,
        )

    @bee.command(name="list")
    @vbu.defer()
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

        # Make the components to send
        components = vbu.MessageComponents(vbu.ActionRow(
            vbu.Button("Breed some of your bees", custom_id="RUNCOMMAND bee breed", style=vbu.ButtonStyle.SECONDARY),
            vbu.Button("Add one of your queens to a hive", custom_id="RUNCOMMAND hive add", style=vbu.ButtonStyle.SECONDARY),
        ))
        return await ctx.send(
            embed=embed,
            allowed_mentions=discord.AllowedMentions.none(),
            components=components,
            wait=False,
        )

    @bee.command(name="rename")
    @vbu.defer()
    async def bee_rename(self, ctx: vbu.Context, before: utils.Bee = None, *, after: str = None):
        """
        Renames one of your bees.
        """

        # Set up our send method
        send_method = ctx.send

        # Check name length
        if after is None or len(after) < 1:
            return await send_method(content="That bee name is too short!")
        if len(after) > 50:
            return await send_method(content="That bee name is too long!")

        # See if they gave a bee
        if not before:
            payload, _, before = await utils.Bee.send_bee_dropdown(
                ctx=ctx, send_method=send_method, current_message=None,
                group_by_nobility=True, group_by_type=True,
            )
            if not before:
                return
            else:
                before = before[0]
            if payload:
                send_method = payload.update_message

        # Save bee
        async with self.bot.database() as db:
            try:
                await before.update(db, name=after)
            except asyncpg.UniqueViolationError:
                return await send_method(
                    content=f"You already have a bee with the name **{after}**! >:c",
                    allowed_mentions=discord.AllowedMentions.none(),
                    components=None,
                )
        return await send_method(content="Updated!", components=None)

    @bee.command(name="release")
    @vbu.defer()
    async def bee_release(self, ctx: vbu.Context, *, bee: utils.Bee = None):
        """
        Releases one of your bees back into the wild.
        """

        # Set up our send method
        send_method = ctx.send

        # If they didn't give a bee then give them a dropdown
        if bee is None:
            payload, _, bees = await utils.Bee.send_bee_dropdown(
                ctx=ctx, send_method=send_method, current_message=None, group_by_nobility=True,
                group_by_type=True, max_values=25,
            )
            if not bees:
                return
            await payload.defer_update()
            send_method = payload.message.edit
            bee_ids = [i.id for i in bees]

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
    async def bee_breed(self, ctx: vbu.Context):
        """
        Breed one of your princesses and drones into a queen.
        """

        # Set the send method
        send_method = ctx.send

        # Get the princess
        payload, current_message, bees = await utils.Bee.send_bee_dropdown(
            ctx=ctx, send_method=send_method, current_message=None, group_by_nobility=True,
            group_by_type=True, check=lambda bee: bee.nobility == utils.Nobility.PRINCESS,
            content="Which princess would you like to breed?",
        )
        if not bees:
            return
        send_method = payload.update_message
        princess = bees[0]

        # Get the drone
        payload, current_message, bees = await utils.Bee.send_bee_dropdown(
            ctx=ctx, send_method=send_method, current_message=current_message, group_by_nobility=True,
            group_by_type=True, check=lambda bee: bee.nobility == utils.Nobility.DRONE,
            content="Which drone would you like to breed?",
        )
        send_method = payload.update_message
        drone = bees[0]

        # Defer the response
        await payload.defer_update()
        send_method = payload.message.edit

        # Breed the bee
        async with self.bot.database() as db:
            try:
                new_bee = await utils.Bee.breed(db, princess, drone)
            except ValueError:
                return await send_method(content="You can't breed anything other than a drone and a princess! :<", components=None)

            # Store our cross-bred types
            await db(
                """INSERT INTO user_bee_combinations (guild_id, user_id, left_type, right_type, result_type)
                VALUES ($1, $2, $3, $4, $5) ON CONFLICT DO NOTHING""",
                utils.get_bee_guild_id(ctx), ctx.author.id, *sorted([princess.type.value, drone.type.value]),
                new_bee.type.value,
            )

        # Tell the user about their new queen
        return await send_method(
            content=(
                f"Your {princess.type.value} princess and {drone.type.value} drone got "
                f"together and made a new {new_bee.type.value} queen, **{new_bee.display_name}**! :D"
            ),
            components=vbu.MessageComponents(vbu.ActionRow(
                vbu.Button("Add your queen to a hive", custom_id="RUNCOMMAND hive add", style=vbu.ButtonStyle.SECONDARY),
            )),
            allowed_mentions=discord.AllowedMentions.none(),
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
            current_user_bees = await utils.Bee.fetch_bees_by_user(db, utils.get_bee_guild_id(ctx), ctx.author.id)

        # Generate our starting DOT lines
        mundane_count = 0
        mundane_output = []
        mundane_output.append((
            "style=rounded;"
            "node[color=red,margin=0.05,shape=ellipse];"
        ))
        added_joiners = set()
        output = []
        output.append((
            # "rankdir=LR;"
            "overlap=scale;"
            "compound=true;"
            "splines=false;"
            "node[color=transparent,margin=0.03,shape=box,height=0.001,width=0.001];"
        ))

        # Make some DOT for each of the user's current bees
        for bee in current_user_bees:
            left = bee.type
            if left.is_mundane:
                v = f"\"{left.value.title()} Bee\";"
                if v not in output:
                    mundane_output.append(v)

        # Make some DOT for each of our combinations
        for row in bee_rows:

            # See if it's a cross-breed combo
            left = utils.BeeType.get(row['left_type'])
            right = utils.BeeType.get(row['right_type'])
            result = utils.BeeType.get(row['result_type'])
            if left == right:
                continue
            if result.is_mundane:
                continue
            if result in [left, right]:
                continue

            # See if the breed is real
            expected_result = utils.BeeType.combine(left, right, return_all_types=True)
            if not isinstance(expected_result, (list, tuple)):
                expected_result = [expected_result]
            if result not in expected_result:
                continue

            # Make our actual DOT
            joiner = f"{left.value}{right.value}"
            if left.is_mundane:
                v = f"\"{left.value.title()} Bee\";"
                if v not in mundane_output:
                    mundane_output.append(v)
            if right.is_mundane:
                v = f"\"{right.value.title()} Bee\";"
                if v not in mundane_output:
                    mundane_output.append(v)
            if [left.is_mundane, right.is_mundane].count(True) == 2:
                if "mundanemundane" in added_joiners:
                    continue
                v = (
                    f"mundanemundane[label=\"\",height=0.001,width=0.001,color=black,shape=point];"
                    f"mundane{{}}->mundanemundane[dir=none,ltail=cluster_0];"
                    f"mundane{{}}->mundanemundane[dir=none,ltail=cluster_0];"
                    f"mundanemundane->\"{result.value.title()} Bee\";"
                )
                output.append(v.format(mundane_count + 1, mundane_count + 2))
                added_joiners.add("mundanemundane")
                mundane_count += 2
            elif [left.is_mundane, right.is_mundane].count(True) == 1 and utils.BeeType.get("CULTIVATED") == result:
                if left.is_mundane:
                    joiner = f"mundane{right.value.lower()}"
                    if joiner in added_joiners:
                        continue
                    v = (
                        f"{joiner}[label=\"\",height=0.001,width=0.001,color=black,shape=point];"
                        f"mundane{{}}->{joiner}[dir=none,ltail=cluster_0];"
                        f"\"{right.value.title()} Bee\"->{joiner}[dir=none];"
                        f"{joiner}->\"{result.value.title()} Bee\";"
                    )
                    output.append(v.format(mundane_count + 1))
                    added_joiners.add(joiner)
                    mundane_count += 1
                else:
                    joiner = f"mundane{left.value.lower()}"
                    if joiner in added_joiners:
                        continue
                    v = (
                        f"{joiner}[label=\"\",height=0.001,width=0.001,color=black,shape=point];"
                        f"\"{left.value.title()} Bee\"->{joiner}[dir=none];"
                        f"mundane{{}}->{joiner}[dir=none,ltail=cluster_0];"
                        f"{joiner}->\"{result.value.title()} Bee\";"
                    )
                    output.append(v.format(mundane_count + 1))
                    added_joiners.add(joiner)
                    mundane_count += 1
            else:
                output.append((
                    f"{joiner}[label=\"\",height=0.001,width=0.001,color=black,shape=point];"
                    f"\"{left.value.title()} Bee\"->{joiner}[dir=none];"
                    f"\"{right.value.title()} Bee\"->{joiner}[dir=none];"
                    f"{joiner}->\"{result.value.title()} Bee\";"
                ))

        # See if we have an output
        try:
            sections = len(mundane_output) - 1 // mundane_count
            for i in range(mundane_count):
                mundane_output.insert((sections * i // 2), f"mundane{i + 1}[shape=point,margin=0,height=0.001,width=0.001];")
        except Exception:
            pass
        output.insert(1, f"subgraph cluster_0{{{''.join(mundane_output)}}};")
        if len(output) <= 2:
            return await ctx.send("You've not cross-bred any bees yet :<")

        # Write the dot to a file
        dot_filename = f'./.{ctx.author.id}.dot'
        try:
            output_string = "".join(output)
            with open(dot_filename, 'w', encoding='utf-8') as a:
                a.write(f"digraph{{{output_string}}}\n")
        except Exception as e:
            self.logger.error(f"Could not write to {dot_filename}")
            raise e

        # Convert to an image
        image_filename = f'./.{ctx.author.id}.png'
        format_rendering_option = '-Tpng:cairo'
        dot = await asyncio.create_subprocess_exec('dot', format_rendering_option, dot_filename, '-o', image_filename, '-Gcharset=UTF-8')
        # dot = await asyncio.create_subprocess_exec('neato', format_rendering_option, dot_filename, '-o', image_filename, '-Gcharset=UTF-8')
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

    @bee.command(name="tree")
    @vbu.defer()
    async def bee_tree(self, ctx: vbu.Context, bee: utils.Bee = None):
        """
        Map out the family tree for a given bee.
        """

        # Set the send method
        send_method = ctx.send

        # See if they gave a bee
        if not bee:
            payload, _, bee = await utils.Bee.send_bee_dropdown(
                ctx=ctx, send_method=send_method, current_message=None,
                group_by_nobility=True, group_by_type=True,
            )
            if not bee:
                return
            else:
                bee = bee[0]
            if payload:
                send_method = payload.update_message

        # Grab all the bees that have ever been in that bee's family
        bee_parent_ids = bee.parent_ids
        bees = {bee.id: bee}
        async with self.bot.database() as db:
            while bee_parent_ids:
                rows = await db(
                    """SELECT * FROM bees WHERE guild_id = $1 AND id = ANY($2::TEXT[])""",
                    utils.get_bee_guild_id(ctx), bee_parent_ids,
                )
                new_bees = {i['id']: utils.Bee(**i) for i in rows}
                bee_parent_ids = []
                for b in new_bees.values():
                    bee_parent_ids.extend(b.parent_ids)
                bees.update(new_bees)

        # Generate our starting DOT lines
        output = []
        output.append((
            "overlap=scale;"
            "compound=true;"
            "splines=true;"
            "node[color=transparent,margin=0.03,shape=box,height=0.001,width=0.001];"
        ))

        # And add our bee friends
        for bee in bees.values():
            bee_name = bee.display_name.replace('"', '\\"')
            output.append((
                f"BEE_{bee.id.replace('-', '_')}[label=\"{bee_name}\\n({bee.display_type})\"];"
            ))
            for parent_id in bee.parent_ids:
                parent = bees[parent_id]
                bee_name = parent.display_name.replace('"', '\\"')
                output.append((
                    f"BEE_{parent.id.replace('-', '_')}[label=\"{bee_name} ({parent.display_type})\"];"
                    f"BEE_{parent.id.replace('-', '_')}->BEE_{bee.id.replace('-', '_')};"
                ))

        # Write the dot to a file
        dot_filename = f'./.{ctx.author.id}.dot'
        try:
            output_string = "".join(output)
            with open(dot_filename, 'w', encoding='utf-8') as a:
                a.write(f"digraph{{{output_string}}}\n")
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
