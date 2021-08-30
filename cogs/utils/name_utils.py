import random
import pathlib


NAMES_FILE_PATH = pathlib.Path("./config/names.txt")
with open(NAMES_FILE_PATH) as a:
    NAMES = a.read().strip().split("\n")


def get_random_name() -> str:
    return random.choice(NAMES)
