import typing
import random
import uuid
import asyncio

import discord
from discord.ext import commands
import voxelbotutils as vbu

from .bee import Bee
from .item import Item, Inventory
from .hive_cell_emoji import HiveCellEmoji


HIVE_NAMES = [
    "Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India",
    "Juliet", "Kilo", "Lima", "Mike", "November", "Oscar", "Papa", "Quebec", "Romeo",
    "Sierra", "Tango", "Uniform", "Victor", "Whiskey", "Xray", "Yankee", "Zulu",
]


class Hive(object):

    SLASH_COMMAND_ARG_TYPE = vbu.ApplicationCommandOptionType.STRING

    __slots__ = (
        'id', 'index', 'guild_id', 'owner_id', 'bees', 'inventory',
    )

    def __init__(self, id: str, index: int, guild_id: int, owner_id: int):
        self.id: str = id
        self.index: int = index
        self.guild_id: int = guild_id
        self.owner_id: int = owner_id
        self.bees: typing.Set[Bee] = set()
        self.inventory: Inventory = Inventory()

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
                """
                SELECT
                    h.*, b.id bee_id
                FROM
                    hives h
                LEFT JOIN
                    bees b
                ON
                    h.id = b.hive_id
                WHERE
                    index = $1
                    AND h.guild_id = $2
                    AND h.owner_id = $3
                """,
                hive_index, ctx.guild.id, ctx.author.id,
            )
            if not hive_rows:
                raise commands.BadArgument(f"You don't have a hive with the name **{value}**.")

            # Grab the items in the hive
            inventory_rows = await db(
                """
                SELECT
                    *
                FROM
                    hive_inventory
                WHERE
                    hive_id = $1
                """,
                hive_rows[0]['id'],
            )

            # Grab the first row so that we can make a hive from it
            hive_row = dict(hive_rows[0])
            hive_row.pop("bee_id", None)  # Remove the bee ID so we can just unpack it
            hive = cls(**hive_row)

            # Parse the inventory items
            for row in inventory_rows:
                hive.inventory[row['item_name']] += row['quantity']

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
    async def fetch_hives_by_user(
            cls, db, guild_id: int, user_id: int, *, fetch_bees: bool = True,
            fetch_inventory: bool = True) -> typing.List['Hive']:
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

        # Get inventory
        if fetch_inventory:
            inventory_rows = await db(
                """SELECT * FROM hive_inventory WHERE hive_id=ANY($1::TEXT[])""",
                hives.keys(),
            )
            for r in inventory_rows:
                hive = hives[r['hive_id']]
                hive.inventory[r['item_name']] += r['quantity']

        # And return the hives
        return hives.values()

    def get_hive_grid(self, width: int = 9, height: int = 9):
        r = random.Random(int(uuid.UUID(self.id).hex, 16))
        return HiveCellEmoji.get_grid(width, height, random=r)

    @classmethod
    async def send_hive_dropdown(
            cls, ctx: vbu.Context, send_method, current_message: discord.Message,
            check=None) -> typing.Tuple[vbu.ComponentInteractionPayload, discord.Message, 'Hive']:
        """
        Send a dropdown to let a user pick one of their hives.
        """

        # Grab the bees
        async with ctx.bot.database() as db:
            hives = await cls.fetch_hives_by_user(db, ctx.guild.id, ctx.author.id)

        # Make sure a check exists
        if check is None:
            check = lambda _: True  # noqa

        # Get the check
        hives = {i.id: i for i in hives if check(i)}

        # Make sure there are bees
        if not hives:
            current_message = await send_method(content="You have no available hives :<", components=None) or current_message
            return (None, current_message, None,)

        # Make components
        components = vbu.MessageComponents(
            vbu.ActionRow(vbu.SelectMenu(
                custom_id="HIVE_SELECTION",
                options=[
                    vbu.SelectOption(label=hive.name, value=hive.id)
                    for hive in hives.values()
                ],
                placeholder="Which hive would you like to choose?"
            )),
            vbu.ActionRow(vbu.Button(
                label="Cancel",
                custom_id="CANCEL",
                style=vbu.ButtonStyle.DANGER,
            )),
        )

        # Send message
        current_message = await send_method(content="Which hive would you like to choose?", components=components) or current_message

        # Wait for interaction
        try:
            payload = await ctx.bot.wait_for("component_interaction", check=vbu.component_check(ctx.author, current_message), timeout=60)
        except asyncio.TimeoutError:
            current_message = await send_method(content="I timed out waiting for you to select a hive :c", components=None) or current_message
            return (None, current_message, None,)

        # See if it were cancelled
        if payload.component.custom_id == "CANCEL":
            current_message = await payload.update_message(content="Cancelled your hive selection :<", components=None) or current_message
            return (payload, current_message, None,)

        # Return the bee
        specified_bee = hives[payload.values[0]]
        return (payload, current_message, specified_bee,)

