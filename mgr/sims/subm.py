from dataclasses import dataclass
from typing import Any
from enum import Enum, auto
from random import choice


@dataclass
class Pair:
    x: int = 0
    y: int = 0

    def __add__(self, other):
        return Pair(self.x + other.x, self.y + other.y)


class Move(Enum):
    LEFT = auto(Pair(-1, 0))
    RIGHT = auto(Pair(1, 0))
    UP = auto(Pair(0, 1))
    DOWN = auto(Pair(0, -1))
    NO_MOVE = auto(Pair(0, 0))


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
