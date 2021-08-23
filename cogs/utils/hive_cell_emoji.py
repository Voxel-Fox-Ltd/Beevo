import random as random_module


class HiveCellEmoji(object):

    all_cells = set()

    def __init__(self, emoji, flags, weight: int = 100):
        self.emoji = emoji
        self.flags = flags
        self.weight = weight
        self.all_cells.add(self)

    @classmethod
    def get_cell(cls, flags, noflags, *, random: random_module.Random = None):
        valid_cells = [i for i in cls.all_cells if set(i.flags).issuperset(set(flags)) and not set(i.flags).intersection(set(noflags))]
        return (random_module or random).choices(valid_cells, weights=[i.weight for i in valid_cells], k=1)[0]

    @classmethod
    def get_grid(cls, width: int = 9, height: int = 9, *, random: random_module.Random = None):
        """
        Make a grid of hive cell emojis.
        """

        # Make our initial grid
        grid = [[None for inner in range(width)] for outer in range(height)]

        # Go through each grid cell
        for y in range(0, height):
            for x in range(0, width):

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
                if x == width - 1:
                    nosearch_cells.add("HAS_RIGHT")
                if y == 0:
                    nosearch_cells.add("HAS_TOP")
                if y == height - 1:
                    nosearch_cells.add("HAS_BOTTOM")

                # Find a relevant cell
                new_cell = cls.get_cell(search_cells, nosearch_cells, random=random)
                grid[y][x] = new_cell

        # Join and return
        output_lines = list()
        for i in grid:
            output_lines.append("".join([o.emoji for o in i]))
        return "\n".join(output_lines)


HiveCellEmoji("<:HiveCell:864882083884171264>", ["HAS_MIDDLE", "HAS_TOP", "HAS_LEFT", "HAS_RIGHT", "HAS_BOTTOM"], weight=100)
HiveCellEmoji("<:HiveCellMissingTop:864882084023894027>", ["HAS_LEFT", "HAS_MIDDLE", "HAS_RIGHT", "HAS_BOTTOM"], weight=90)
HiveCellEmoji("<:HiveCellMissingRight:864883719676231680>", ["HAS_LEFT", "HAS_MIDDLE", "HAS_TOP", "HAS_BOTTOM"], weight=90)
HiveCellEmoji("<:HiveCellMissingMiddle:864882083884171267>", ["HAS_LEFT", "HAS_TOP", "HAS_BOTTOM", "HAS_RIGHT"], weight=90)
HiveCellEmoji("<:HiveCellMissingLeft:864883719664173098>", ["HAS_TOP", "HAS_BOTTOM", "HAS_MIDDLE", "HAS_RIGHT"], weight=90)
HiveCellEmoji("<:HiveCellMissingBottom:864882084195205180>", ["HAS_MIDDLE", "HAS_TOP", "HAS_LEFT", "HAS_RIGHT"], weight=90)
HiveCellEmoji("<:HiveCellMissingTopBottom:864883719398752297>", ["HAS_LEFT", "HAS_MIDDLE", "HAS_RIGHT"], weight=40)
HiveCellEmoji("<:HiveCellMissingSides:864883719797735454>", ["HAS_MIDDLE", "HAS_TOP", "HAS_BOTTOM"], weight=40)
HiveCellEmoji("<:HiveCellOnlyTop:865091796420788284>", ["HAS_MIDDLE", "HAS_TOP"], weight=30)
HiveCellEmoji("<:HiveCellOnlyRight:865091796023246868>", ["HAS_MIDDLE", "HAS_RIGHT"], weight=30)
HiveCellEmoji("<:HiveCellOnlyLeft:865091796186955828>", ["HAS_MIDDLE", "HAS_LEFT"], weight=30)
HiveCellEmoji("<:HiveCellOnlyBottom:865091795797016596>", ["HAS_MIDDLE", "HAS_BOTTOM"], weight=30)
HiveCellEmoji("<:HiveCellOnlyMiddle:865094728940126218>", ["HAS_MIDDLE"], weight=30)
HiveCellEmoji("<:HiveCellEmpty:865094728420294676>", [], weight=10)
HiveCellEmoji("<:HiveCellMissingCornerTR:864883719779909672>", ["HAS_MIDDLE", "HAS_LEFT", "HAS_BOTTOM"], weight=10)
HiveCellEmoji("<:HiveCellMissingCornerTL:864883719613448202>", ["HAS_MIDDLE", "HAS_RIGHT", "HAS_BOTTOM"], weight=10)
HiveCellEmoji("<:HiveCellMissingCornerBR:864883719664173096>", ["HAS_MIDDLE", "HAS_TOP", "HAS_LEFT"], weight=10)
HiveCellEmoji("<:HiveCellMissingCornerBL:864882083762274364>", ["HAS_MIDDLE", "HAS_TOP", "HAS_RIGHT"], weight=10)
