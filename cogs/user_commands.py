import voxelbotutils as vbu
import discord
from discord.ext import commands

from cogs import utils


class UserCommands(vbu.Cog):

    @vbu.command()
    @vbu.defer()
    @commands.guild_only()
    async def inventory(self, ctx: vbu.Context, user: discord.Member = None):
        """
        Get the inventory for a given user.
        """

        user = user or ctx.author
        async with self.bot.database() as db:
            inventory_rows = await db(
                """SELECT * FROM user_inventory WHERE guild_id = $1 AND user_id = $2 AND quantity > 0""",
                ctx.guild.id, user.id,
            )
        if not inventory_rows:
            return await ctx.send(
                utils.format(
                    "{0:pronoun,You,{1}} {0:pronoun,have,has} nothing in {0:pronoun,your,their} inventory :<",
                    ctx.author == user,
                    user.mention,
                ),
                wait=False,
            )

        inventory = [utils.Item(**i) for i in inventory_rows]
        embed = vbu.Embed(use_random_colour=True)
        embed.set_author_to_user(user=user)
        embed.description = "\n".join([
            f"\N{BULLET} {i.name} x{i.quantity}" for i in inventory
        ])
        return await ctx.send(embed=embed, wait=False)


def setup(bot: vbu.Bot):
    x = UserCommands(bot)
    bot.add_cog(x)
