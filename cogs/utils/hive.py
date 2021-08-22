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
        'id', 'index', 'guild_id', 'owner_id', 'bees',
    )

    def __init__(self, id: str, index: int, guild_id: int, owner_id: int):
        self.id: str = id
        self.index: int = index
        self.guild_id: int = guild_id
        self.owner_id: int = owner_id
        self.bees: typing.Set[Bee] = set()

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

            # Grab the hive and the bees in it
            hive_rows = await db(
                """SELECT h.*, b.id bee_id FROM hives h LEFT JOIN bees b ON h.id=b.hive_id
                WHERE index=$1 AND h.guild_id=$2 AND h.owner_id=$3""",
                hive_index, ctx.guild.id, ctx.author.id,
            )
            if not hive_rows:
                raise commands.BadArgument(f"You don't have a hive with the name **{value}**.")

            # Grab the first row so that we can make a hive from it
            hive_row = dict(hive_rows[0])
            hive_row.pop("bee_id", None)  # Remove the bee ID so we can just unpack it
            hive = cls(**hive_row)

            # Grab all the bees that are in the hive
            bee_ids = [i['bee_id'] for i in hive_rows]
            bee_rows = await db(
                """SELECT * FROM bees WHERE id=ANY($1::TEXT[])""",
                bee_ids,
            )
            for row in bee_rows:
                bee = Bee(**row)
                bee.hive = hive
                hive.bees.add(bee)

        # Return the hive object
        return hive

    @classmethod
    async def fetch_hives_by_user(cls, db, guild_id: int, user_id: int, *, fetch_bees: bool = True) -> typing.List['Hive']:
        """
        Get all the hives for a given user.
        """

        # Get hives
        hive_rows = await db(
            """SELECT h.*, b.id bee_id FROM hives h LEFT JOIN bees b ON h.id=b.hive_id
            WHERE h.guild_id=$1 AND h.owner_id=$2""",
            guild_id, user_id,
        )
        hives = {}
        bee_ids = []
        for r in hive_rows:
            r = dict(r)
            bee_id = r.pop('bee_id', None)
            hive = cls(**r)
            if bee_id:
                bee_ids.append(bee_id)
            hives[hive.id] = hive

        # Get bees
        if fetch_bees:
            bee_rows = await db(
                """SELECT * FROM bees WHERE id=ANY($1::TEXT[])""",
                bee_ids,
            )
            for r in bee_rows:
                bee = Bee(**r)
                hive = hives[bee.hive_id]
                hive.bees.add(bee)
                bee.hive = hive

        # And return the hives
        return hives.values()

