from dataclasses import dataclass
from enum import Enum
from random import choice
from typing import Any


@dataclass
class Pair:
    x: int = 0
    y: int = 0

    def __add__(self, other):
        return Pair(self.x + other.x, self.y + other.y)


class Move(Enum):
    LEFT = Pair(-1, 0)
    RIGHT = Pair(1, 0)
    UP = Pair(0, 1)
    DOWN = Pair(0, -1)
    NO_MOVE = Pair(0, 0)


@dataclass
class Code:
    username: str
    top: Pair | None = None
    bot: Pair | None = None

    def get_move(self, context: Any) -> Move | None:
        return choice(tuple(Move))


@dataclass
class PrisonCode:
    username: str

    def get_move(self, context: Any) -> str:
        return "Wspolpraca"
