import pathlib
import random

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
            bee = await utils.Bee.create_bee(db, ctx.author.id, nobility=utils.Nobility.DRONE)
            bee.name = random.choice(self.names)
            await bee.update(db)
        return await ctx.send(f"Created your new {bee.type.value.lower()} drone **{bee.display_name}**!")

    @vbu.command()
    async def getprincess(self, ctx: vbu.Context):
        """
        Generate a test bee for you to flirt with.
        """

        async with self.bot.database() as db:
            bee = await utils.Bee.create_bee(db, ctx.author.id, nobility=utils.Nobility.PRINCESS)
            bee.name = random.choice(self.names)
            await bee.update(db)
        return await ctx.send(f"Created your new {bee.type.value.lower()} princess **{bee.display_name}**!")

    @vbu.command()
    async def listbees(self, ctx: vbu.Context):
        """
        Shows you all of the bees you have
        """

        async with self.bot.database() as db:
            bees = await utils.Bee.fetch_bees_by_user(db, ctx.author.id)
        if not bees:
            return await ctx.send("You don't have any bees! :c")
        bee_string = "\n".join([f"\\* **{i.display_name}** ({i.type.value.lower()} {i.nobility.value.lower()})" for i in bees])
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

    @vbu.command()
    async def releasebee(self, ctx: vbu.Context, bee: utils.Bee):
        """
        Releases one of your bees back into the wild.
        """

        async with self.bot.database() as db:
            await bee.delete(db)
        return await ctx.send(f"Released **{bee.display_name}** into the wild \N{PENSIVE FACE}")

    @vbu.command()
    async def petbee(self, ctx: vbu.Context, bee: utils.Bee):
        """
        Pet one of your bees on their fluffy lil heads.
        """

        return await ctx.send(f"**{bee.display_name}**: *Happy buzzing noises* \N{HONEYBEE}")


def setup(bot: vbu.Bot):
    x = BeeCommands(bot)
    bot.add_cog(x)
