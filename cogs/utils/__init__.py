import voxelbotutils as _vbu

from .bee import Bee, BeeType, Nobility  # noqa
from .hive import Hive  # noqa
from .item import Item, Inventory  # noqa
from .hive_cell_emoji import HiveCellEmoji  # noqa
from .utils import *  # noqa


_vbu.Formatter.EMOJI_EMPTY = "<:ExpEmpty:879144403325812776>"
_vbu.Formatter.EMOJI_QUARTER = "<:ExpQuarter:879147649381568532>"
_vbu.Formatter.EMOJI_HALF = "<:ExpHalf:879144403321622539>"
_vbu.Formatter.EMOJI_THREE_QUARTERS = "<:ExpQuarter3:879147649364819999>"
_vbu.Formatter.EMOJI_FULL = "<:ExpFull:879144403325812777>"
