from dataclasses import dataclass
from typing import Literal

from mgr.exec import BaseExecutor


@dataclass
class Subm:
    id: int
    code: str
    lang: Literal["CPP", "PY"]


Status = Literal[
    "oczekiwanie",
    "kompilacja",
    "błąd kompilacji",
    "testowanie",
    "błąd testowania",
    "ok",
]

EXC_TIMEOUT=0.5
EXC_MEM_LIMIT=64


class Simulator():
    def test(self, exec: BaseExecutor):
        # TODO: if compilation error, then raise ExecutionError
        #       and prevent executor from raising its error here
        pass