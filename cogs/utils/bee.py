import typing
import enum
import uuid
import random
import pathlib

from discord.ext import commands
import voxelbotutils as vbu


NAMES_FILE_PATH = pathlib.Path("./config/names.txt")


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
    def get_mundane_bees(cls):
        for i in cls.get_all_bees():
            if isinstance(i, MundaneBeeType):
                yield i

    @classmethod
    def get_all_bees(cls):
        items = dir(cls)
        for i in items:
            if not i.isupper():
                continue
            x = getattr(cls, i)
            if isinstance(x, BeeType):
                yield x

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

    with open(NAMES_FILE_PATH) as a:
        NAMES = a.read().strip().split("\n")

    __slots__ = (
        '_id', 'parent_ids', 'guild_id', 'owner_id', 'name', '_type',
        '_nobility', 'speed', 'fertility', 'generation',
    )

    def __init__(
            self, id: typing.Union[str, uuid.UUID], parent_ids: typing.List[typing.Union[str, uuid.UUID]],
            nobility: typing.Union[str, Nobility], speed: int, fertility: int, owner_id: int,
            generation: int, name: str, type: typing.Union[str, BeeType], guild_id: int):

        #: The ID of this bee.
        self.id: str = id  # Added as _id

        #: The IDs of this bee's parents - can be empty but cannot be null.
        self.parent_ids: typing.List[str] = parent_ids or list()

        #: The guild that this bee belongs to.
        self.guild_id: int = guild_id

        #: The owner of this particular bee.
        self.owner_id: int = owner_id

        #: The name that the owner gave to this bee.
        self.name: str = name

        #: The type of bee that this is
        self.type: BeeType = type  # Added as _type

        #: The nobility of this bee - this says if it's a queen, princess, or drone.
        self.nobility: Nobility = nobility  # Added as _nobility

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
    async def breed(cls, db, mother: 'Bee', father: 'Bee'):
        """
        Breed two bees together to make a queen, which will be automatically added to the user, as well
        as both parents being removed from the user.
        Raises a ValueError if one bee is not a princess and one bee is not a drone.
        """

        # Make sure the nobilities are correct
        if {mother.nobility.value, father.nobility.value} != {Nobility.DRONE.value, Nobility.PRINCESS.value}:
            raise ValueError()

        # Work out which bee is which
        princess = [i for i in [mother, father] if i.nobility == Nobility.PRINCESS][0]
        drone = [i for i in [mother, father] if i.nobility == Nobility.DRONE][0]

        # Pick some new stats for it
        speed = random.randint(
            max(min(princess.speed, drone.speed) - 2, 0),
            max(princess.speed, drone.speed) + 5,
        )
        fertility = random.randint(
            max(min(princess.fertility, drone.fertility) - 2, 0),
            max(princess.fertility, drone.fertility) + 5,
        )
        new_bee = await cls.create_bee(
            db=db,
            guild_id=princess.guild_id,
            user_id=princess.owner_id,
            bee_type=BeeType.combine(princess.type, drone.type),
            nobility=Nobility.QUEEN,
        )
        await new_bee.update(db, speed=speed, fertility=fertility, parent_ids=[princess.id, drone.id])
        await princess.update(db, owner_id=None)
        await drone.update(db, owner_id=None)
        return new_bee

    @classmethod
    def get_random_name(cls):
        return random.choice(cls.NAMES)

    @classmethod
    async def fetch_bee_by_id(cls, bee_id: str):
        ...

    @classmethod
    async def fetch_bees_by_user(cls, db, guild_id: int, user_id: int) -> typing.List['Bee']:
        """
        Gives you a list of the bees owned by the given user.
        """

        rows = await db("""SELECT * FROM bees WHERE owner_id=$1 AND guild_id=$2""", user_id, guild_id)
        return [cls(**i) for i in rows]

    @classmethod
    async def create_bee(cls, db, guild_id: int, user_id: int, bee_type: BeeType = None, nobility: Nobility = Nobility.DRONE):
        """
        Create a new bee.
        """

        bee_type = bee_type or random.choice(list(BeeType.get_mundane_bees()))
        rows = await db(
            """INSERT INTO bees (id, guild_id, owner_id, type, nobility, name) VALUES
            (GEN_RANDOM_UUID()::TEXT, $1, $2, $3, $4, $5) RETURNING *""",
            guild_id, user_id, bee_type.value, nobility.value, cls.get_random_name(),
        )
        return cls(**rows[0])

    async def update(self, db, **kwargs):
        """
        Create a new bee.
        """

        for i, o in kwargs.items():
            setattr(self, i, o)
        await db(
            """UPDATE bees SET parent_ids=$2, owner_id=$3, name=$4, nobility=$5,
            speed=$6, fertility=$7, generation=$8, type=$9, guild_id=$10 WHERE id=$1""",
            self.id, self.parent_ids, self.owner_id, self.name,
            self.nobility.value, self.speed, self.fertility, self.generation,
            self.type.value, self.guild_id,
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
                """SELECT * FROM bees WHERE owner_id=$1 AND (id=$2 OR LOWER(name)=LOWER($2)) AND guild_id=$3""",
                ctx.author.id, value, ctx.guild.id,
            )
        if not rows:
            raise commands.BadArgument("You don't have a bee with that name!")
        return cls(**rows[0])
