import pathlib
import random

import voxelbotutils as vbu
from discord.ext import commands

from cogs import utils


NAMES_FILE_PATH = pathlib.Path("./config/names.txt")


class BeeCommands(vbu.Cog):

    def __init__(self, bot: vbu.Bot):
        super().__init__(bot)
        with open(NAMES_FILE_PATH) as a:
            self.names = a.read().strip().split("\n")

    @vbu.command()
    @vbu.cooldown.cooldown(1, 60 * 60, commands.BucketType.user)
    @commands.guild_only()
    async def getbees(self, ctx: vbu.Context):
        """
        Catch some new bees for your hive.
        """

        async with self.bot.database() as db:
            drone = await utils.Bee.create_bee(db, ctx.guild.id, ctx.author.id, nobility=utils.Nobility.DRONE)
            drone.name = random.choice(self.names)
            await drone.update(db)
            princess = await utils.Bee.create_bee(db, ctx.guild.id, ctx.author.id, nobility=utils.Nobility.PRINCESS)
            princess.name = random.choice(self.names)
            await princess.update(db)
        return await ctx.send((
            f"Created your new bees: a {drone.type.value.lower()} drone, **{drone.display_name}**; "
            f"and a {princess.type.value.lower()} princess, **{princess.display_name}**!"
        ))

    @vbu.command(aliases=['list'])
    @commands.guild_only()
    async def listbees(self, ctx: vbu.Context):
        """
        Shows you all of the bees you have
        """

        async with self.bot.database() as db:
            bees = await utils.Bee.fetch_bees_by_user(db, ctx.guild.id, ctx.author.id)
        if not bees:
            return await ctx.send("You don't have any bees! :c")
        bee_string = "\n".join([f"\\* **{i.display_name}** ({i.type.value.lower()} {i.nobility.value.lower()})" for i in bees])
        return await ctx.send(f"You have {len(bees)} bees: \n{bee_string}")

    @vbu.command(aliases=['rename'])
    @commands.guild_only()
    async def renamebee(self, ctx: vbu.Context, before: utils.Bee, after: str):
        """
        Renames one of your bees.
        """

        async with self.bot.database() as db:
            before.name = after
            await before.update(db)
        return await ctx.send("Updated!")

    @vbu.command(aliases=['release'])
    @commands.guild_only()
    async def releasebee(self, ctx: vbu.Context, bee: utils.Bee):
        """
        Releases one of your bees back into the wild.
        """

        async with self.bot.database() as db:
            bee.owner_id = None
            await bee.update(db)
        return await ctx.send(f"Released **{bee.display_name}** into the wild \N{PENSIVE FACE}")

    @vbu.command(aliases=['pet'])
    @commands.guild_only()
    async def petbee(self, ctx: vbu.Context, bee: utils.Bee):
        """
        Pet one of your bees on their fluffy lil heads.
        """

        return await ctx.send(f"**{bee.display_name}**: *Happy buzzing noises* \N{HONEYBEE}")


def setup(bot: vbu.Bot):
    x = BeeCommands(bot)
    bot.add_cog(x)
