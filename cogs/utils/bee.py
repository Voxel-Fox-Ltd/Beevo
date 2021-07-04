import typing
import enum
import uuid


class Nobility(enum.Enum):
    DRONE = 'Drone'
    PRINCESS = 'Princess'
    QUEEN = 'Queen'


class Bee(object):

    def __init__(
            self, id: typing.Union[str, uuid.UUID], parent_ids: list[typing.Union[str, uuid.UUID]],
            nobility: typing.Union[str, Nobility], speed: int, fertility: int, owner_id: int,
            generation: int, name: str):

        #: The ID of this bee.
        self.id: str = id

        #: The IDs of this bee's parents - can be empty but cannot be null.
        self.parent_ids: list[str] = parent_ids or list()

        #: The owner of this particular bee
        self.owner_id: int = owner_id

        #: The name that the owner gave to this bee
        self.name: str = name

        #: The nobility of this bee - this says if it's a queen, princess, or drone.
        self.nobility: str = nobility

        #: How quickly this bee can produce honey. Only used for queens but can be bred down from anywhere.
        self.speed: int = speed

        #: How many drones this bee produces when it dies. Only used for queens but can be bred down from anywhere.
        self.fertility: int = fertility

        #: How many generations old this bee is.
        self.generation: int = generation

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

    @classmethod
    def breed(cls, mother: 'Bee', father: 'Bee'):
        ...

    @classmethod
    async def fetch_bee_by_id(cls, bee_id: str):
        ...

    @classmethod
    async def create_bee(cls, db, user_id: int = None):
        """
        Create a new bee.
        """

        rows = await db(
            """INSERT INTO bees (id, owner_id) VALUES (GEN_RANDOM_UUID(), $1) RETURNING *""",
            user_id,
        )
        return cls(**rows[0])

    async def update(self, db):
        """
        Create a new bee.
        """

        await db(
            """UPDATE bees SET parent_ids=$2, owner_id=$3, name=$4, nobility=$5,
            speed=$6, fertility=$7, generation=$8 WHERE id=$1""",
            self.id, self.parent_ids, self.owner_id, self.name,
            self.nobility, self.speed, self.fertility, self.generation
        )
