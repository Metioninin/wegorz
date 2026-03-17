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
    
    def get_move(self, context: Any) -> Move | None:
        return choice(tuple(Move))