import pathlib
import random

from discord.ext import commands
import voxelbotutils as vbu

from cogs import utils


NAMES_FILE_PATH = pathlib.Path("./config/names.txt")


class BeeCommands(vbu.Cog):

    def __init__(self, bot: vbu.Bot):
        super().__init__(bot)
        with open(NAMES_FILE_PATH) as a:
            self.names = a.read().strip().split("\n")

    @vbu.command()
    async def getdrone(self, ctx: vbu.Context):
        """
        Generate a test bee for you to flirt with.
        """

        async with self.bot.database() as db:
            bee = await utils.Bee.create_bee(db, ctx.author.id)
            bee.name = random.choice(self.names)
            await bee.update(db)
        return await ctx.send(f"Created your bee! `{bee.name or bee.id}`")

    @vbu.command()
    async def listbees(self, ctx: vbu.Context):
        """
        Shows you all of the bees you have
        """

        async with self.bot.database() as db:
            bees = await utils.Bee.fetch_bees_by_user(db, ctx.author.id)
        if not bees:
            return await ctx.send("You don't have any bees! :c")
        bee_string = "\n".join([f"\\* **{i.name or i.id}**" for i in bees])
        return await ctx.send(f"You have {len(bees)} bees: \n{bee_string}")

    @vbu.command()
    async def renamebee(self, ctx: vbu.Context, before: utils.Bee, after: str):
        """
        Renames one of your bees.
        """

        async with self.bot.database() as db:
            before.name = after
            await before.update(db)
        return await ctx.send("Updated!")


def setup(bot: vbu.Bot):
    x = BeeCommands(bot)
    bot.add_cog(x)
