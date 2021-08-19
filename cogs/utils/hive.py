import typing

from discord.ext import commands
import voxelbotutils as vbu


HIVE_NAMES = [
    "Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India",
    "Juliet", "Kilo", "Lima", "Mike", "November", "Oscar", "Papa", "Quebec", "Romeo",
    "Sierra", "Tango", "Uniform", "Victor", "Whiskey", "Xray", "Yankee", "Zulu",
]


class Hive(object):

    SLASH_COMMAND_ARG_TYPE = vbu.ApplicationCommandOptionType.STRING

    __slots__ = (
        'id', 'index', 'guild_id', 'owner_id',
    )

    def __init__(self, id: str, index: int, guild_id: int, owner_id: int):
        self.id: str = id
        self.index: int = index
        self.guild_id: int = guild_id
        self.owner_id: int = owner_id

    @property
    def name(self) -> str:
        return HIVE_NAMES[self.index]

    @classmethod
    async def convert(cls, ctx: vbu.Context, value: str):
        """
        The Discord convert method for hives.
        """

        try:
            hive_index = HIVE_NAMES.index(value.title())
        except ValueError:
            raise commands.BadArgument(f"**{value}** isn't a valid hive name.")
        async with ctx.bot.database() as db:
            rows = await db(
                """SELECT * FROM hives WHERE index=$1 AND guild_id=$2 AND owner_id=$3""",
                hive_index, ctx.guild.id, ctx.author.id,
            )
        if not rows:
            raise commands.BadArgument(f"You don't have a hive with the name **{value}**.")
        return cls(**rows[0])
