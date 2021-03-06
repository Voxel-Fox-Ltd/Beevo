import typing
import enum
import random
import math
import asyncio

import asyncpg
import discord
from discord.ext import commands
import voxelbotutils as vbu

from .name_utils import get_random_name
from .utils import get_bee_guild_id


class Nobility(enum.Enum):
    DRONE = 'Drone'
    PRINCESS = 'Princess'
    QUEEN = 'Queen'


class BeeType(object):

    BEE_COMBINATIONS = {}
    BEE_TYPE_VALUES = {}
    BEE_TYPE_COMBS = {}

    def __init__(self, value: str):
        self.name = value.upper()
        self.value = value.lower()

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"{self.__class__.__name__}('{self.name}')"

    @classmethod
    def get_mundane_bees(cls):
        for i in cls.get_all_bees():
            if isinstance(i, MundaneBeeType):
                yield i

    @property
    def is_mundane(self):
        return isinstance(self, MundaneBeeType)

    @classmethod
    def get_all_bees(cls):
        items = dir(cls)
        for i in items:
            if i == ["BEE_COMBINATIONS", "BEE_TYPE_VALUES", "BEE_TYPE_COMBS"]:
                continue
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

    def get_comb(self) -> str:
        return self.BEE_TYPE_COMBS[self]

    def get_value(self) -> int:
        return self.BEE_TYPE_VALUES[self]

    def get_comb_value(self) -> int:
        this_comb = self.get_comb()
        return min((o for i, o in self.BEE_TYPE_VALUES.items() if i.get_comb() == this_comb))

    @staticmethod
    def check_if_matches(item, comparable):
        """
        See if an object matches the base class (which may be an object).
        """

        try:
            return isinstance(item, comparable)
        except TypeError:
            return item.name == comparable.name

    @classmethod
    def combine(cls, first: 'BeeType', second: 'BeeType', *, return_all_types: bool = False):
        """
        Combine two bees and give the child type.
        """

        # If they're two of the same, just send the first back
        if first.value == second.value:
            return first

        # Let's see how the combinations line up
        for (i, o), v in cls.BEE_COMBINATIONS.items():
            checks = [
                cls.check_if_matches(first, i) and cls.check_if_matches(second, o),
                cls.check_if_matches(first, o) and cls.check_if_matches(second, i),
            ]
            if any(checks):
                if isinstance(v, (list, tuple)) and not return_all_types:
                    return random.choice(v)
                return v
        return random.choice([first, second])


class MundaneBeeType(BeeType):
    pass


class ComplexBeeType(BeeType):
    pass


def setup_bee_types():
    """
    Set up the bee types that the bot uses.
    """

    # Mundane bees
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

    # Complex bees
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

    # Bee combinations
    BeeType.BEE_COMBINATIONS = {
        # (MundaneBeeType, MundaneBeeType,): BeeType.get("COMMON"),
        (BeeType.get("COMMON"), MundaneBeeType,): BeeType.get("CULTIVATED"),
        (BeeType.get("COMMON"), BeeType.get("CULTIVATED"),): [BeeType.get("NOBLE"), BeeType.get("DILLIGENT")],
        (BeeType.get("NOBLE"), BeeType.get("CULTIVATED"),): BeeType.get("IMPERIAL"),
        (BeeType.get("DILLIGENT"), BeeType.get("CULTIVATED"),): BeeType.get("UNWEARY"),
        (BeeType.get("DILLIGENT"), BeeType.get("UNWEARY"),): BeeType.get("INDUSTRIOUS"),
        (BeeType.get("STEADFAST"), BeeType.get("VALIANT"),): BeeType.get("HEROIC"),
        (BeeType.get("MODEST"), BeeType.get("CULTIVATED"),): BeeType.get("SINISTER"),
        (BeeType.get("TROPICAL"), BeeType.get("CULTIVATED"),): BeeType.get("SINISTER"),
        (BeeType.get("MODEST"), BeeType.get("SINISTER"),): BeeType.get("FIENDISH"),
        (BeeType.get("CULTIVATED"), BeeType.get("SINISTER"),): BeeType.get("FIENDISH"),
        (BeeType.get("TROPICAL"), BeeType.get("SINISTER"),): BeeType.get("FIENDISH"),
        (BeeType.get("FIENDISH"), BeeType.get("SINISTER"),): BeeType.get("DEMONIC"),
        (BeeType.get("MODEST"), BeeType.get("SINISTER"),): BeeType.get("FRUGAL"),
        (BeeType.get("MODEST"), BeeType.get("FIENDISH"),): BeeType.get("FRUGAL"),
        (BeeType.get("MODEST"), BeeType.get("FRUGAL"),): BeeType.get("AUSTERE"),
        (BeeType.get("AUSTERE"), BeeType.get("TROPICAL"),): BeeType.get("EXOTIC"),
        (BeeType.get("EXOTIC"), BeeType.get("TROPICAL"),): BeeType.get("EDENIC"),
        (BeeType.get("INDUSTRIOUS"), BeeType.get("WINTRY"),): BeeType.get("ICY"),
        (BeeType.get("ICY"), BeeType.get("WINTRY"),): BeeType.get("GLACIAL"),
        (BeeType.get("MEADOWS"), BeeType.get("DILLIGENT"),): BeeType.get("RURAL"),
    }
    for left in BeeType.get_mundane_bees():
        for right in BeeType.get_mundane_bees():
            if left == right:
                continue
            BeeType.BEE_COMBINATIONS.update({(left, right,): BeeType.get("COMMON")})

    # Bee values
    for i in BeeType.get_mundane_bees():
        BeeType.BEE_TYPE_VALUES[i] = 1
    for _ in range(5):
        for (left, right), result in BeeType.BEE_COMBINATIONS.items():
            if not isinstance(result, (list, tuple)):
                result = [result]
            for r in result:
                BeeType.BEE_TYPE_VALUES[r] = max(
                    BeeType.BEE_TYPE_VALUES.get(left, 1),
                    BeeType.BEE_TYPE_VALUES.get(right, 1),
                ) + 1

    # Bee combs
    BeeType.BEE_TYPE_COMBS = {
        BeeType.get("FOREST"): "honey",
        BeeType.get("MEADOWS"): "honey",
        BeeType.get("MODEST"): "parched",
        BeeType.get("TROPICAL"): "silky",
        BeeType.get("WINTRY"): "frozen",
        BeeType.get("MARSHY"): "mossy",
        BeeType.get("WATER"): "wet",
        BeeType.get("ROCKY"): "rocky",
        BeeType.get("EMBITTERED"): "simmering",
        BeeType.get("MARBLED"): "honey",
        BeeType.get("VALIANT"): "cocoa",
        BeeType.get("STEADFAST"): "cocoa",
        BeeType.get("COMMON"): "honey",
        BeeType.get("CULTIVATED"): "honey",
        BeeType.get("NOBLE"): "dripping",
        BeeType.get("MAJESTIC"): "dripping",
        BeeType.get("IMPERIAL"): "dripping",
        BeeType.get("DILLIGENT"): "stringy",
        BeeType.get("UNWEARY"): "stringy",
        BeeType.get("INDUSTRIOUS"): "stringy",
        BeeType.get("HEROIC"): "cocoa",
        BeeType.get("SINISTER"): "simmering",
        BeeType.get("FIENDISH"): "simmering",
        BeeType.get("DEMONIC"): "simmering",
        BeeType.get("FRUGAL"): "parched",
        BeeType.get("AUSTERE"): "parched",
        BeeType.get("EXOTIC"): "silky",
        BeeType.get("EDENIC"): "silky",
        BeeType.get("ICY"): "frozen",
        BeeType.get("GLACIAL"): "frozen",
        BeeType.get("RURAL"): "wheaten",
    }


setup_bee_types()


class Bee(object):

    SLASH_COMMAND_ARG_TYPE = vbu.ApplicationCommandOptionType.STRING

    __slots__ = (
        'id', 'parent_ids', 'guild_id', 'owner_id', 'name', '_type',
        '_nobility', 'speed', 'fertility', 'hive_id',
        'hive', 'lifetime', 'lived_lifetime',
    )

    def __init__(
            self, id: str, parent_ids: typing.List[str], hive_id: str,
            nobility: typing.Union[str, Nobility], speed: int, fertility: int,
            owner_id: int, name: str, type: typing.Union[str, BeeType],
            guild_id: int, lifetime: int, lived_lifetime: int):

        #: The ID of this bee.
        self.id: str = id

        #: The IDs of this bee's parents - can be empty but cannot be null.
        self.parent_ids: typing.List[str] = parent_ids or list()

        #: The guild that this bee belongs to.
        self.guild_id: int = guild_id

        #: The owner of this particular bee.
        self.owner_id: int = owner_id

        #: The ID of the hive that this bee lives in.
        self.hive_id: str = hive_id

        #: The hive object that this bee lives in.
        self.hive: 'Hive' = None

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

        #: How many ticks this bee stays alive for when it's in a hive.
        self.lifetime: int = lifetime

        #: How many ticks this bee has been in a hive for.
        self.lived_lifetime: int = lived_lifetime

    @property
    def display_name(self):
        return self.name or self.id

    @property
    def display_type(self):
        return f"{self.type.value.lower()} {self.nobility.value.lower()}"

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
            self._type = BeeType.get(value)

    @staticmethod
    def get_new_stats(mother, father=None) -> dict:
        """
        Get some new stats for the given bee.
        """

        speed = random.randint(
            max(math.floor(min(mother.speed, (father or mother).speed) * 0.5), 1),  # always have at least a 1% chance of making honey
            min(math.ceil(max(mother.speed, (father or mother).speed) * 1.5), 200),  # max 5 a tick
        )
        fertility = random.randint(
            max(math.floor(min(mother.fertility, (father or mother).fertility) * 0.5), 1),  # always leave 1 bee
            min(math.ceil(max(mother.fertility, (father or mother).fertility) * 1.2), 3),  # max 10 bees
        )
        lifetime = random.randint(
            max(math.floor(min(mother.lifetime, (father or mother).lifetime) * 0.75), 60),  # 5 minutes
            min(math.ceil(max(mother.lifetime, (father or mother).lifetime) * 1.25), 720),  # 1 hour
        )
        return {
            "speed": speed,
            "fertility": fertility,
            "lifetime": lifetime,
        }

    @classmethod
    async def breed(cls, db, mother: 'Bee', father: 'Bee'):
        """
        Breed two bees together to make a queen, which will be automatically added to the user, as well
        as both parents being removed from the user.
        Raises a ValueError if one bee is not a princess and one bee is not a drone.
        """

        # Make sure the nobilities are correct
        if {mother.nobility, father.nobility} != {Nobility.DRONE, Nobility.PRINCESS}:
            raise ValueError()

        # Work out which bee is which
        princess = [i for i in [mother, father] if i.nobility == Nobility.PRINCESS][0]
        drone = [i for i in [mother, father] if i.nobility == Nobility.DRONE][0]

        # Pick some new stats for it
        new_stats = cls.get_new_stats(mother, father)
        new_bee = await cls.create_bee(
            db=db,
            guild_id=princess.guild_id,
            user_id=princess.owner_id,
            bee_type=BeeType.combine(princess.type, drone.type),
            nobility=Nobility.QUEEN,
        )
        await princess.update(db, owner_id=None)
        await new_bee.update(db, **new_stats, name=princess.name, parent_ids=[princess.id, drone.id])
        await drone.update(db, owner_id=None)
        return new_bee

    async def die(self, db) -> typing.List['Bee']:
        """
        Have this bee die, leaving behind a princess and a series of drones.
        """

        # Only queens can perish
        if self.nobility != Nobility.QUEEN:
            raise ValueError()

        # Generate our new bees
        def make_new_bee(nobility):
            v = self.__class__(
                id=None,
                parent_ids=[self.id],
                hive_id=self.hive_id,
                nobility=nobility,
                owner_id=self.owner_id,
                name=None,
                type=self.type,
                guild_id=self.guild_id,
                lived_lifetime=0,
                **self.get_new_stats(self),
            )
            v.hive = self.hive
            return v
        new_bees = [make_new_bee(Nobility.PRINCESS)]
        new_bees.extend((make_new_bee(Nobility.DRONE) for _ in range(self.fertility)))

        # Add a comb to the hive
        await db(
            """
            INSERT INTO
                hive_inventory
                (hive_id, item_name, quantity)
            VALUES
                ($1, INITCAP($2 || ' Comb'), 1)
            ON CONFLICT
                (hive_id, item_name)
            DO UPDATE SET
                quantity = hive_inventory.quantity + excluded.quantity
            """,
            self.hive_id, self.type.get_comb(),
        )

        # Update (kill) our current bee
        self.owner_id = None
        self.hive_id = None
        await self.update(db)

        # Save the new bees to database
        new_bees[0].name = self.name
        for bee in new_bees:
            await bee.update(db)

        # And return the new ones
        return new_bees

    @classmethod
    async def fetch_bee_by_id(cls, db, bee_id: str) -> typing.Optional['Bee']:
        """
        Get a bee instance by its ID.
        """

        rows = await db("""SELECT * FROM bees WHERE id=$1""", bee_id)
        try:
            return cls(**rows[0])
        except IndexError:
            return None

    @classmethod
    async def fetch_bees_by_user(cls, db, guild_id: int, user_id: int) -> typing.List['Bee']:
        """
        Gives you a list of the bees owned by the given user.
        """

        rows = await db("""SELECT * FROM bees WHERE owner_id = $1 AND guild_id = $2""", user_id, guild_id)
        return [cls(**i) for i in rows]

    @classmethod
    async def create_bee(cls, db, guild_id: int, user_id: int, bee_type: BeeType = None, nobility: Nobility = Nobility.DRONE) -> 'Bee':
        """
        Create a new bee.
        """

        bee_type = bee_type or random.choice(list(BeeType.get_mundane_bees()))
        while True:
            try:
                rows = await db(
                    """INSERT INTO bees (id, guild_id, owner_id, type, nobility, name) VALUES
                    (GEN_RANDOM_UUID()::TEXT, $1, $2, $3, $4, $5) RETURNING *""",
                    guild_id, user_id, bee_type.value, nobility.value, get_random_name(),
                )
            except asyncpg.UniqueViolationError:
                pass
            else:
                break
        return cls(**rows[0])

    async def update(self, db, **kwargs):
        """
        Create a new bee.
        """

        for i, o in kwargs.items():

            # See if we set a hive ID
            if i == "hive_id":
                if self.hive and self.hive.id != o:
                    self.hive = None
                self.hive_id = o

            # See if we set a hive
            elif i == "hive":
                if o:
                    self.hive_id = o.id
                else:
                    self.hive_id = None
                self.hive = o

            # Anything else is fine
            else:
                setattr(self, i, o)

        # Make sure we have some fields
        if self.id is None:
            new_bee = await self.create_bee(db, self.guild_id, self.owner_id)
            self.id = new_bee.id
            self.name = self.name or new_bee.name
        if self.name is None:
            self.name = get_random_name()

        # And database
        await db(
            """
            UPDATE
                bees
            SET
                parent_ids = $2,
                owner_id = $3,
                name = $4,
                nobility = $5,
                speed = $6,
                fertility = $7,
                type = $8,
                guild_id = $9,
                hive_id = $10,
                lifetime = $11,
                lived_lifetime = $12
            WHERE
                id = $1
            """,
            self.id, self.parent_ids, self.owner_id, self.name,
            self.nobility.value, self.speed, self.fertility,
            self.type.value, self.guild_id, self.hive_id,
            self.lifetime, self.lived_lifetime,
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
                ctx.author.id, value, get_bee_guild_id(ctx),
            )
        if not rows:
            raise commands.BadArgument("You don't have a bee with that name!")
        return cls(**rows[0])

    @classmethod
    async def send_bee_dropdown(
            cls, ctx: vbu.Context, send_method, current_message: discord.Message, max_values: int = 1, *,
            group_by_nobility: bool = False, group_by_type: bool = False, check=None,
            content: str = None, no_available_bees_content: str = None) -> typing.Tuple[vbu.ComponentInteractionPayload, discord.Message, typing.List['Bee']]:
        """
        Send a dropdown to let a user pick one of their bees.
        """

        # Grab the bees
        async with ctx.bot.database() as db:
            bees = await cls.fetch_bees_by_user(db, get_bee_guild_id(ctx), ctx.author.id)

        # Make sure a check exists
        if check is None:
            check = lambda _: True  # noqa

        # Get the check
        bees = {i.id: i for i in bees if check(i)}

        # Make sure there are bees
        if not bees:
            no_available_bees_content = no_available_bees_content or "You have no available bees :<"
            current_message = await send_method(content=no_available_bees_content, components=None) or current_message
            return (None, current_message, None,)

        # See if we want to group by royalty
        if group_by_nobility:
            if len(set([i.nobility for i in bees.values()])) > 1:
                queens = {i: o for i, o in bees.items() if o.nobility == Nobility.QUEEN}
                princesses = {i: o for i, o in bees.items() if o.nobility == Nobility.PRINCESS}
                drones = {i: o for i, o in bees.items() if o.nobility == Nobility.DRONE}

                # Ask what kind of bee they want to get rid of
                components = vbu.MessageComponents(
                    vbu.ActionRow(
                        vbu.Button("Queen", custom_id="CHOOSE_QUEEN", disabled=not bool(queens)),
                        vbu.Button("Princess", custom_id="CHOOSE_PRINCESS", disabled=not bool(princesses)),
                        vbu.Button("Drone", custom_id="CHOOSE_DRONES", disabled=not bool(drones)),
                    ),
                    vbu.ActionRow(
                        vbu.Button("Cancel", custom_id="CANCEL", style=vbu.ButtonStyle.DANGER)
                    ),
                )
                current_message = await send_method(
                    content="What kind of bee would you like to choose?",
                    components=components,
                ) or current_message
                try:
                    payload = await ctx.bot.wait_for("component_interaction", check=vbu.component_check(ctx.author, current_message), timeout=60)
                except asyncio.TimeoutError:
                    current_message = await send_method(
                        content="I timed out waiting for you to say what nobility of bee you want to select :<",
                        components=None,
                    ) or current_message
                    return (None, current_message, None,)
                if payload.component.custom_id == "CHOOSE_QUEEN":
                    bees = queens
                elif payload.component.custom_id == "CHOOSE_PRINCESS":
                    bees = princesses
                elif payload.component.custom_id == "CHOOSE_DRONES":
                    bees = drones
                else:
                    current_message = await payload.update_message(content="Cancelled your bee selection :<", components=None) or current_message
                    return (payload, current_message, None,)
                send_method = payload.update_message

        # See if we want to group by type
        if group_by_type:
            bee_types = sorted(list(set([o.type.value for o in bees.values()])))
            if len(bee_types) > 1:
                components = vbu.MessageComponents(
                    vbu.ActionRow(
                        vbu.SelectMenu(
                            custom_id="BEE_SELECTION",
                            options=[
                                vbu.SelectOption(label=i.title(), value=i)
                                for i in bee_types
                            ],
                            placeholder="What type of bee would you like to select?",
                        ),
                    ),
                    vbu.ActionRow(
                        vbu.Button("Cancel", custom_id="CANCEL", style=vbu.ButtonStyle.DANGER),
                    ),
                )
                current_message = await send_method(content="What type of bee would you like to select?", components=components) or current_message
                try:
                    payload = await ctx.bot.wait_for("component_interaction", check=vbu.component_check(ctx.author, current_message), timeout=60)
                except asyncio.TimeoutError:
                    current_message = await send_method(
                        content="I timed out waiting for you to what bee you want to select :c",
                        components=None,
                    ) or current_message
                if payload.component.custom_id == "CANCEL":
                    current_message = await payload.update_message(content="Cancelled your bee selection :<", components=None) or current_message
                    return (payload, current_message, None,)
                send_method = payload.update_message
                bees = {i: o for i, o in bees.items() if o.type.value.casefold() == payload.values[0].casefold()}

        # Make components
        components = vbu.MessageComponents(
            vbu.ActionRow(vbu.SelectMenu(
                custom_id="BEE_SELECTION",
                options=[
                    vbu.SelectOption(label=bee.name, value=bee.id, description=bee.display_type.capitalize())
                    for bee in list(bees.values())[:25]
                ],
                max_values=min(max_values, len(bees), 25),
                placeholder="Which bee would you like to choose?"
            )),
            vbu.ActionRow(vbu.Button(
                label="Cancel",
                custom_id="CANCEL",
                style=vbu.ButtonStyle.DANGER,
            )),
        )

        # Send message
        content = content or "Which bee would you like to choose?"
        current_message = await send_method(content=content, components=components) or current_message

        # Wait for interaction
        try:
            payload = await ctx.bot.wait_for("component_interaction", check=vbu.component_check(ctx.author, current_message), timeout=60)
        except asyncio.TimeoutError:
            current_message = await send_method(content="I timed out waiting for you to select a bee :c", components=None) or current_message
            return (None, current_message, None,)

        # See if it were cancelled
        if payload.component.custom_id == "CANCEL":
            current_message = await payload.update_message(content="Cancelled your bee selection :<", components=None) or current_message
            return (payload, current_message, None,)

        # Return the bee
        specified_bees = [bees[i] for i in payload.values]
        return (payload, current_message, specified_bees,)
