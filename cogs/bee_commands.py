import collections

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
                f"Created your new bees: a {drone.type.value.lower()} drone, **{drone.display_name}**; "
                f"and a {princess.type.value.lower()} princess, **{princess.display_name}**!"
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
        formatter = lambda bee: f"\N{BULLET} **{bee.display_name}** ({bee.type.value.lower()} {bee.nobility.value.lower()})"  # noqa
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
    async def bee_release(self, ctx: vbu.Context, bee: utils.Bee):
        """
        Releases one of your bees back into the wild.
        """

        async with self.bot.database() as db:
            bee.owner_id = None
            await bee.update(db)
        return await ctx.send(
            f"Released **{bee.display_name}** into the wild \N{PENSIVE FACE}",
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
    @commands.guild_only()
    async def bee_breed(self, ctx: vbu.Context, princess: utils.Bee, drone: utils.Bee):
        """
        Breed one of your princesses and drones into a queen.
        """

        # Defer our response because we love database lag
        await ctx.defer()

        # Breed the bee
        async with self.bot.database() as db:
            try:
                new_bee = await utils.Bee.breed(db, princess, drone)
            except ValueError:
                return await ctx.send("You can't breed anything other than a drone and a princess! :<", wait=False)

        # Tell the user about their new queen
        return await ctx.send(
            f"Your princess and drone got together and made a new {new_bee.type.value} queen, **{new_bee.display_name}**! :D",
            allowed_mentions=discord.AllowedMentions.none(),
            wait=False,
        )


def setup(bot: vbu.Bot):
    x = BeeCommands(bot)
    bot.add_cog(x)
