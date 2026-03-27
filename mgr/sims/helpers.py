from dataclasses import dataclass
from enum import Enum, StrEnum
from random import choice
from typing import Any

from mgr.exec import BaseExecutor, ExecutionError
from mgr.helpers import wrap_err


class TestError(Exception):
    pass


@dataclass
class Pair:
    x: int = 0
    y: int = 0

    def __add__(self, other):
        return Pair(self.x + other.x, self.y + other.y)


class AgarioMove(Enum):
    LEFT = Pair(-1, 0)
    RIGHT = Pair(1, 0)
    UP = Pair(0, 1)
    DOWN = Pair(0, -1)
    NO_MOVE = Pair(0, 0)


class PrisonMove(StrEnum):
    COOPERATE = "Wspolpraca"
    BETRAY = "Niezgoda"


@dataclass
class Code:
    username: str
    top: Pair | None = None
    bot: Pair | None = None

    def get_move(self, context: Any) -> AgarioMove | None:
        return choice(tuple(AgarioMove))


@dataclass
class Prisoner:
    username: str
    exc: BaseExecutor | None  # NOTE: must be started before

    def send_start_info(self, enemy_name: str) -> None:
        assert self.exc
        self.exc.send_line(f"{enemy_name}")

    @property
    def crashed(self):
        return not self.exc or self.exc._proc is None

    def get_move(self, raise_errors: bool = False) -> PrisonMove | None:
        assert self.exc

        try:
            out = self.exc.read_string()
        except ExecutionError as e:
            if raise_errors:
                raise TestError(str(e))
            return None

        if out in PrisonMove:
            return PrisonMove(out)

        self.exc.exit()
        self.exc = None

        if raise_errors:
            raise TestError(
                f"Niepoprawny ruch: {wrap_err(out)}"
            )
        return None


class FakePrisoner(Prisoner):
    def __init__(self):
        super().__init__(username="0", exc=None)

    def send_start_info(self, *args, **kwargs) -> None:
        pass

    def get_move(self, *args, **kwargs) -> PrisonMove:
        return PrisonMove.COOPERATE


todelete = ["Fold", "Raise 10", "Call"]
@dataclass
class PokerCode:
    username: str

    def get_move(self, context: Any) -> str:
        return choice(todelete)