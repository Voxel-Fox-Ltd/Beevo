import discord
from discord.ext import commands, vbu

from cogs import utils


class UserCommands(vbu.Cog):

    @vbu.command()
    @commands.defer()
    async def inventory(self, ctx: vbu.Context, user: discord.Member = None):
        """
        Get the inventory for a given user.
        """

        user = user or ctx.author
        async with vbu.Database() as db:
            inventory_rows = await db(
                """SELECT * FROM user_inventory WHERE guild_id = $1 AND user_id = $2 AND quantity > 0""",
                utils.get_bee_guild_id(ctx), user.id,
            )
        if not inventory_rows:
            return await ctx.send(
                vbu.format(
                    "{0:pronoun,You,{1}} {0:pronoun,have,has} nothing in {0:pronoun,your,their} inventory :<",
                    ctx.author == user,
                    user.mention,
                ),
            )

        inventory = [utils.Item(**i) for i in inventory_rows]
        embed = vbu.Embed(use_random_colour=True)
        embed.set_author_to_user(user=user)
        embed.description = "\n".join([
            f"\N{BULLET} {i.name} x{i.quantity}" for i in inventory
        ])
        return await ctx.send(embed=embed)


def setup(bot: vbu.Bot):
    x = UserCommands(bot)
    bot.add_cog(x)
