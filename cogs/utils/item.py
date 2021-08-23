import collections


class Item(object):

    def __init__(self, item_name: str, quantity: int, **kwargs):
        self.item_name = item_name
        self.quantity = quantity

    @property
    def name(self):
        return self.item_name

    @name.setter
    def name(self, value: str):
        self.item_name = value

    def __add__(self, other):
        if isinstance(other, int):
            return self.__class__(self.name, self.quantity + other)
        elif isinstance(other, self.__class__):
            if self.name != other.name:
                raise ValueError()
            return self.__class__(self.name, self.quantity + other.quantity)
        else:
            raise TypeError()


class Inventory(collections.defaultdict):

    def __missing__(self, key):
        self[key] = Item(key, 0)
        return self[key]
