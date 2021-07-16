import voxelbotutils as vbu

from cogs import utils


class HiveCommands(vbu.Cog):

    WIDTH = 9
    HEIGHT = 9

    @vbu.command()
    async def hive(self, ctx):
        """
        Generate a cute lil beehive for you.
        """

        grid = [[None for inner in range(self.WIDTH)] for outer in range(self.HEIGHT)]

        # Go through each grid cell
        for y in range(0, self.HEIGHT):
            for x in range(0, self.WIDTH):

                # Set up our filters
                search_cells = set()
                nosearch_cells = set()

                # See if there's a cell above
                if y:
                    above = grid[y - 1][x]
                    if "HAS_BOTTOM" in above.flags:
                        search_cells.add("HAS_TOP")
                    else:
                        nosearch_cells.add("HAS_TOP")

                # See if there's a cell to the left
                if x:
                    left = grid[y][x - 1]
                    if "HAS_RIGHT" in left.flags:
                        search_cells.add("HAS_LEFT")
                    else:
                        nosearch_cells.add("HAS_LEFT")

                # See if we're EDGING BABY
                if x == 0:
                    nosearch_cells.add("HAS_LEFT")
                if x == WIDTH - 1:
                    nosearch_cells.add("HAS_RIGHT")
                if y == 0:
                    nosearch_cells.add("HAS_TOP")
                if y == HEIGHT - 1:
                    nosearch_cells.add("HAS_BOTTOM")

                # Find a relevant cell
                new_cell = utils.HiveCellEmoji.get_cell(search_cells, nosearch_cells)
                grid[y][x] = new_cell

        output_lines = list()
        for i in grid:
            output_lines.append("".join([o.emoji for o in i]))
        await ctx.send(embed=vbu.Embed(description="\n".join(output_lines)))


def setup(bot: vbu.Bot):
    x = HiveCommands(bot)
    bot.add_cog(x)
