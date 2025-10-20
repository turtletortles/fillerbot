from enum import Enum

class Colors(Enum):
    red, green, yellow, blue, purple, black, empty = range(7)

class Tile:
    def __init__(self, _color: Colors, _x: int, _y: int, _owner=-1):
        self.color = _color
        self.x = _x
        self.y = _y
        self.owner = _owner

    def copy(self):
        new_tile = Tile(Colors(self.color), self.x, self.y)
        new_tile.owner = self.owner
        return new_tile

