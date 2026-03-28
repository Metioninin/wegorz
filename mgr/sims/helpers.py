from dataclasses import dataclass, field
from enum import Enum, StrEnum
from random import choice, randint
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
            raise TestError(f"Niepoprawny ruch: {wrap_err(out)}")
        return None


class FakePrisoner(Prisoner):
    def __init__(self):
        super().__init__(username="0", exc=None)

    def send_start_info(self, *args, **kwargs) -> None:
        pass

    def get_move(self, *args, **kwargs) -> PrisonMove:
        return PrisonMove.COOPERATE


@dataclass
class Card:
    kolor: str
    numer: str

    def __str__(self) -> str:
        return self.kolor + " " + self.numer


@dataclass
class PlayerInfo:
    twojIndex: int
    hajs: list[int]
    stawki: list[int]
    stawka: int
    pula: int
    ownCards: list[Card]
    mutualCards: list[Card]

    def gen_lines(self) -> list[str]:
        return [
            f"{self.twojIndex}",
            " ".join(str(h) for h in self.hajs),
            " ".join(str(s) for s in self.stawki),
            f"{self.stawka}",
            f"{self.pula}",
            " ".join(str(c) for c in self.ownCards),
            f"{len(self.mutualCards)}",
            " ".join([str(c) for c in self.mutualCards]),
        ]


@dataclass
class PokerCode:
    username: str
    exc: BaseExecutor | None  # NOTE: must be started before
    trace: bool = False
    _comm: list[str] = field(default_factory=list)

    def _get_move(self, ctx: PlayerInfo, raise_errors: bool) -> tuple[str, int] | None:
        if self.exc is None:
            return None

        for line in ctx.gen_lines():
            self.exc.send_line(line)

            if self.trace:
                self._comm.append(line)

        try:
            first_part = self.exc.read_string()
        except ExecutionError as e:
            if raise_errors:
                raise TestError(str(e))
            return None

        if first_part in ("Fold", "Check", "Call"):
            return (first_part, 0)
        elif first_part not in ("Raise", "All"):
            self.exc.exit()
            self.exc = None

            if raise_errors:
                raise TestError(f"Niepoprawny ruch: {wrap_err(first_part)}")
            return None

        try:
            second_part = self.exc.read_string()
        except ExecutionError as e:
            if raise_errors:
                raise TestError(
                    f"Got {wrap_err(first_part)}, but after that error happend\n{e}"
                )
            return None

        if first_part == "All":
            comb = first_part + " " + second_part
            if second_part == "In":
                return (comb, 0)
            raise TestError(f"Oczekiwano 'All In', otrzymano: {wrap_err(comb)}")

        try:
            val = int(second_part)
            assert val > 0
        except:
            self.exc.exit()
            self.exc = None

            if raise_errors:
                raise TestError(f"Niepoprawny wartość raise: {wrap_err(second_part)}")
            return None
        return (first_part, val)

    def get_move(self, ctx: PlayerInfo, raise_errors: bool) -> tuple[str, int] | None:
        move = self._get_move(ctx, raise_errors)

        if self.trace and move:
            str_move = move[0] + ' ' + str(move[1]) if move[0] == "Raise" else move[0]
            self._comm.append(str_move)

        return move


class FakePoker(PokerCode):
    def __init__(self):
        super().__init__(username="0", exc=None)

    def send_start_info(self, *args, **kwargs) -> None:
        pass

    def get_move(self, ctx: PlayerInfo, *args, **kwargs) -> tuple[str, int] | None:
        moves = [("Fold", 0)]
        i = ctx.twojIndex

        if ctx.hajs[i]:
            moves.append(("All In", 0))

        if ctx.stawka - ctx.stawki[i] <= ctx.hajs[i]:
            moves.append(("Call", 0))

            if ctx.hajs[i] + ctx.stawki[i] >= ctx.stawka:
                moves.append(
                    ("Raise", randint(ctx.stawka, ctx.hajs[i] + ctx.stawki[i]))
                )

        if ctx.stawki[i] == ctx.stawka:
            moves.append(("Check", 0))

        return choice(moves)


# poczatkowe sumy graczy (powinny sumowac sie do 6*1000)
POKER_TESTS = (
    (1000, 1000, 1000, 1000, 1000, 1000),
    (100, 1000, 250, 1000, 50, 3600),
    (0, 125, 50, 1000, 3000, 1825),
)
