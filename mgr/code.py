from dataclasses import dataclass
from typing import Any
from enum import Enum, auto
from random import choice


class Move(Enum):
    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()
    NO_MOVE = auto()


@dataclass
class Code:
    username: str
    top_x: int
    top_y: int
    bot_x: int
    bot_y: int
    def get_move(self, context: Any) -> Move | None:
        return choice(tuple(Move))