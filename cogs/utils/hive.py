import typing

from discord.ext import commands
import voxelbotutils as vbu

from .bee import Bee


HIVE_NAMES = [
    "Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India",
    "Juliet", "Kilo", "Lima", "Mike", "November", "Oscar", "Papa", "Quebec", "Romeo",
    "Sierra", "Tango", "Uniform", "Victor", "Whiskey", "Xray", "Yankee", "Zulu",
]


class Hive(object):

    SLASH_COMMAND_ARG_TYPE = vbu.ApplicationCommandOptionType.STRING

    __slots__ = (
        'id', 'index', 'guild_id', 'owner_id', 'bee',
    )

    def __init__(self, id: str, index: int, guild_id: int, owner_id: int):
        self.id: str = id
        self.index: int = index
        self.guild_id: int = guild_id
        self.owner_id: int = owner_id
        self.bee: Bee = None

    @property
    def name(self) -> str:
        return HIVE_NAMES[self.index]

    @classmethod
    async def convert(cls, ctx: vbu.Context, value: str):
        """
        The Discord convert method for hives.
        """

        # See if the name is real
        try:
            hive_index = HIVE_NAMES.index(value.title())
        except ValueError:
            raise commands.BadArgument(f"**{value}** isn't a valid hive name.")

        # Database time
        async with ctx.bot.database() as db:

            # Grab the hive and the bee in it
            hive_rows = await db(
                """SELECT h.*, b.id bee_id FROM hives h LEFT JOIN bees b ON h.id=b.id
                WHERE index=$1 AND h.guild_id=$2 AND h.owner_id=$3""",
                hive_index, ctx.guild.id, ctx.author.id,
            )
            if not hive_rows:
                raise commands.BadArgument(f"You don't have a hive with the name **{value}**.")
            hive_row = dict(hive_rows[0])

            # Grab the bee
            bee_id = hive_row.pop("bee_id", None)
            if bee_id:
                bee_rows = await db(
                    """SELECT * FROM bees WHERE bee_id=$1""",
                    bee_id,
                )
                bee = Bee(**bee_rows[0])

        # Return the hive object
        v = cls(**hive_row)
        if bee_id:
            bee.hive = v
            v.bee = bee
        return v

    @classmethod
    async def fetch_hives_by_user(cls, db, guild_id: int, user_id: int, *, fetch_bees: bool = True) -> typing.List['Hive']:
        """
        Get all the hives for a given user.
        """

        hive_rows = await db(
            """SELECT h.*, b.id bee_id FROM hives h LEFT JOIN bees b ON h.id=b.id
            WHERE h.guild_id=$1 AND h.owner_id=$2""",
            guild_id, user_id,
        )
        hives = []
        for r in hive_rows:
            hives.append((hive := cls(**r)))
            if (bee_id := r['bee_id']):
                bee_rows = await db(
                    """SELECT * FROM bees WHERE bee_id=$1""",
                    bee_id,
                )
                bee = Bee(**bee_rows[0])
                hive.bee = bee
                bee.hive = hive
        return hives

