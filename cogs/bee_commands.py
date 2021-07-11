import voxelbotutils as vbu
import discord
from discord.ext import commands
import asyncpg

from cogs import utils


class BeeCommands(vbu.Cog):

    def __init__(self, bot: vbu.Bot):
        super().__init__(bot)

    @vbu.command()
    @vbu.cooldown.cooldown(1, 60 * 60, commands.BucketType.user)
    @commands.guild_only()
    async def getbees(self, ctx: vbu.Context):
        """
        Catch some new bees for your hive.
        """

        async with self.bot.database() as db:
            drone = await utils.Bee.create_bee(db, ctx.guild.id, ctx.author.id, nobility=utils.Nobility.DRONE)
            await drone.update(db)
            princess = await utils.Bee.create_bee(db, ctx.guild.id, ctx.author.id, nobility=utils.Nobility.PRINCESS)
            await princess.update(db)
        return await ctx.send(
            (
                f"Created your new bees: a {drone.type.value.lower()} drone, **{drone.display_name}**; "
                f"and a {princess.type.value.lower()} princess, **{princess.display_name}**!"
            ),
            wait=False,
        )

    @vbu.command(aliases=['list'])
    @commands.guild_only()
    async def listbees(self, ctx: vbu.Context):
        """
        Shows you all of the bees you have
        """

        async with self.bot.database() as db:
            bees = await utils.Bee.fetch_bees_by_user(db, ctx.guild.id, ctx.author.id)
        if not bees:
            return await ctx.send("You don't have any bees! :c", wait=False)
        bee_string = "\n".join([f"\N{BULLET} **{i.display_name}** ({i.type.value.lower()} {i.nobility.value.lower()})" for i in bees])
        return await ctx.send(
            f"You have {len(bees)} bees: \n{bee_string}",
            allowed_mentions=discord.AllowedMentions.none(),
            wait=False,
        )

    @vbu.command(aliases=['rename'])
    @commands.guild_only()
    async def renamebee(self, ctx: vbu.Context, before: utils.Bee, *, after: str):
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

    @vbu.command(aliases=['release'])
    @commands.guild_only()
    async def releasebee(self, ctx: vbu.Context, bee: utils.Bee):
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

    @vbu.command(aliases=['pet'])
    @commands.guild_only()
    async def petbee(self, ctx: vbu.Context, bee: utils.Bee):
        """
        Pet one of your bees on their fluffy lil heads.
        """

        return await ctx.send(
            f"**{bee.display_name}**: *Happy buzzing noises* \N{HONEYBEE}",
            allowed_mentions=discord.AllowedMentions.none(),
            wait=False,
        )

    @vbu.command(aliases=['breed'])
    @commands.guild_only()
    async def breedbee(self, ctx: vbu.Context, princess: utils.Bee, drone: utils.Bee):
        """
        Breed one of your princesses and drones into a queen.
        """

        utils.Bee.breed(princess, drone)
        await ctx.send("nice", wait=False)


def setup(bot: vbu.Bot):
    x = BeeCommands(bot)
    bot.add_cog(x)
