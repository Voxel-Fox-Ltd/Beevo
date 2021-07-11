import typing
import enum
import uuid
import random

from discord.ext import commands
import voxelbotutils as vbu


class Nobility(enum.Enum):
    DRONE = 'Drone'
    PRINCESS = 'Princess'
    QUEEN = 'Queen'


class BeeType(object):

    def __init__(self, value: str):
        self.name = value.upper()
        self.value = value.lower()

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.name}')"

    @classmethod
    def get(cls, value: str):
        """
        Get a given bee type.
        """

        return getattr(cls, value.upper(), None)

    @staticmethod
    def check_if_matches(compare, base):
        """
        See if an object matches the base class (which may be an object).
        """

        try:
            return isinstance(compare, base)
        except TypeError:
            return compare.value == base.value

    @classmethod
    def combine(cls, first: 'BeeType', second: 'BeeType'):
        """
        Combine two bees and give the child type.
        """

        # If they're two of the same, just combine em
        if first.value == second.value:
            return cls(first.value)

        # Let's see how the combinations line up
        for (i, o), v in BEE_COMBINATIONS.items():
            checks = [
                cls.check_if_matches(first, i),
                cls.check_if_matches(first, o),
                cls.check_if_matches(second, i),
                cls.check_if_matches(second, o),
            ]
            if checks.count(True) >= 2:
                return v
        return random.choice([first, second])


class MundaneBeeType(BeeType):
    pass


BeeType.FOREST = MundaneBeeType("forest")
BeeType.MEADOWS = MundaneBeeType("meadows")
BeeType.MODEST = MundaneBeeType("modest")
BeeType.TROPICAL = MundaneBeeType("tropical")
BeeType.WINTRY = MundaneBeeType("wintry")
BeeType.MARSHY = MundaneBeeType("marshy")
BeeType.WATER = MundaneBeeType("water")
BeeType.ROCKY = MundaneBeeType("rocky")
BeeType.EMBITTERED = MundaneBeeType("embittered")
BeeType.MARBLED = MundaneBeeType("marbled")
BeeType.STEADFAST = MundaneBeeType("steadfast")
BeeType.VALIANT = MundaneBeeType("valiant")


class ComplexBeeType(BeeType):
    pass


BeeType.COMMON = ComplexBeeType("common")
BeeType.CULTIVATED = ComplexBeeType("cultivated")
BeeType.NOBLE = ComplexBeeType("noble")
BeeType.MAJESTIC = ComplexBeeType("majestic")
BeeType.IMPERIAL = ComplexBeeType("imperial")
BeeType.DILLIGENT = ComplexBeeType("dilligent")
BeeType.UNWEARY = ComplexBeeType("unweary")
BeeType.INDUSTRIOUS = ComplexBeeType("industrious")
BeeType.HEROIC = ComplexBeeType("heroic")
BeeType.SINISTER = ComplexBeeType("sinister")
BeeType.FIENDISH = ComplexBeeType("fiendish")
BeeType.DEMONIC = ComplexBeeType("demonic")
BeeType.FRUGAL = ComplexBeeType("frugal")
BeeType.AUSTERE = ComplexBeeType("austere")
BeeType.EXOTIC = ComplexBeeType("exotic")
BeeType.EDENIC = ComplexBeeType("edenic")
BeeType.ICY = ComplexBeeType("icy")
BeeType.GLACIAL = ComplexBeeType("glacial")
BeeType.RURAL = ComplexBeeType("rural")


BEE_COMBINATIONS = {
    (MundaneBeeType, MundaneBeeType,): BeeType.COMMON,
    (BeeType.COMMON, MundaneBeeType,): BeeType.CULTIVATED,
    (BeeType.COMMON, BeeType.CULTIVATED,): BeeType.NOBLE,
    (BeeType.NOBLE, BeeType.CULTIVATED,): BeeType.IMPERIAL,
    (BeeType.COMMON, BeeType.CULTIVATED,): BeeType.DILLIGENT,
    (BeeType.DILLIGENT, BeeType.CULTIVATED,): BeeType.UNWEARY,
    (BeeType.DILLIGENT, BeeType.UNWEARY,): BeeType.INDUSTRIOUS,
    (BeeType.STEADFAST, BeeType.VALIANT,): BeeType.HEROIC,
    (BeeType.MODEST, BeeType.CULTIVATED,): BeeType.SINISTER,
    (BeeType.TROPICAL, BeeType.CULTIVATED,): BeeType.SINISTER,
    (BeeType.MODEST, BeeType.SINISTER,): BeeType.FIENDISH,
    (BeeType.CULTIVATED, BeeType.SINISTER,): BeeType.FIENDISH,
    (BeeType.TROPICAL, BeeType.SINISTER,): BeeType.FIENDISH,
    (BeeType.FIENDISH, BeeType.SINISTER,): BeeType.DEMONIC,
    (BeeType.MODEST, BeeType.SINISTER,): BeeType.FRUGAL,
    (BeeType.MODEST, BeeType.FIENDISH,): BeeType.FRUGAL,
    (BeeType.MODEST, BeeType.FRUGAL,): BeeType.AUSTERE,
    (BeeType.AUSTERE, BeeType.TROPICAL,): BeeType.EXOTIC,
    (BeeType.EXOTIC, BeeType.TROPICAL,): BeeType.EDENIC,
    (BeeType.INDUSTRIOUS, BeeType.WINTRY,): BeeType.ICY,
    (BeeType.ICY, BeeType.WINTRY,): BeeType.GLACIAL,
    (BeeType.MEADOWS, BeeType.DILLIGENT,): BeeType.RURAL,
}


class Bee(object):

    SLASH_COMMAND_ARG_TYPE = vbu.ApplicationCommandOptionType.STRING

    def __init__(
            self, id: typing.Union[str, uuid.UUID], parent_ids: list[typing.Union[str, uuid.UUID]],
            nobility: typing.Union[str, Nobility], speed: int, fertility: int, owner_id: int,
            generation: int, name: str, type: typing.Union[str, BeeType]):

        #: The ID of this bee.
        self.id: str = id

        #: The IDs of this bee's parents - can be empty but cannot be null.
        self.parent_ids: list[str] = parent_ids or list()

        #: The owner of this particular bee
        self.owner_id: int = owner_id

        #: The name that the owner gave to this bee
        self.name: str = name

        #: The name that the owner gave to this bee
        self.type: str = type

        #: The nobility of this bee - this says if it's a queen, princess, or drone.
        self.nobility: str = nobility

        #: How quickly this bee can produce honey. Only used for queens but can be bred down from anywhere.
        self.speed: int = speed

        #: How many drones this bee produces when it dies. Only used for queens but can be bred down from anywhere.
        self.fertility: int = fertility

        #: How many generations old this bee is.
        self.generation: int = generation

    @property
    def display_name(self):
        return self.name or self.id

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value: typing.Union[str, uuid.UUID]):
        self._id = str(value)

    @property
    def nobility(self):
        return self._nobility

    @nobility.setter
    def nobility(self, value: typing.Union[str, Nobility]):
        if isinstance(value, Nobility):
            self._nobility = value
        else:
            self._nobility = Nobility(value)

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value: typing.Union[str, BeeType]):
        if isinstance(value, BeeType):
            self._type = value
        else:
            self._type = BeeType(value)

    @classmethod
    def breed(cls, mother: 'Bee', father: 'Bee'):
        ...

    @classmethod
    async def fetch_bee_by_id(cls, bee_id: str):
        ...

    @classmethod
    async def fetch_bees_by_user(cls, db, user_id: int) -> list['Bee']:
        """
        Gives you a list of the bees owned by the given user.
        """

        rows = await db("""SELECT * FROM bees WHERE owner_id=$1""", user_id)
        return [cls(**i) for i in rows]

    @classmethod
    async def create_bee(cls, db, user_id: int = None, bee_type: BeeType = None, nobility: Nobility = Nobility.DRONE):
        """
        Create a new bee.
        """

        bee_type = bee_type or random.choice(list(BeeType))
        rows = await db(
            """INSERT INTO bees (id, owner_id, type, nobility) VALUES (GEN_RANDOM_UUID()::TEXT, $1, $2, $3) RETURNING *""",
            user_id, bee_type.value, nobility.value,
        )
        return cls(**rows[0])

    async def update(self, db):
        """
        Create a new bee.
        """

        await db(
            """UPDATE bees SET parent_ids=$2, owner_id=$3, name=$4, nobility=$5,
            speed=$6, fertility=$7, generation=$8, type=$9 WHERE id=$1""",
            self.id, self.parent_ids, self.owner_id, self.name,
            self.nobility.value, self.speed, self.fertility, self.generation,
            self.type.value,
        )

    async def delete(self, db):
        """
        Remove a bee from its owner.
        """

        await db(
            """UPDATE bees SET owner_id=NULL WHERE id=$1""",
            self.id,
        )

    @classmethod
    async def convert(cls, ctx, value: str):
        """
        Get a bee instance from its name.
        """

        async with ctx.bot.database() as db:
            rows = await db(
                """SELECT * FROM bees WHERE owner_id=$1 AND (id=$2 OR name=$2)""",
                ctx.author.id, value,
            )
        if not rows:
            raise commands.BadArgument("You don't have a bee with that name!")
        return cls(**rows[0])
