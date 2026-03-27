from dataclasses import dataclass
from textwrap import shorten
from typing import Literal


@dataclass
class Subm:
    id: int
    code: str
    lang: Literal["CPP", "PY"]
    round_id: int


Status = Literal[
    "oczekiwanie",
    "kompilacja",
    "błąd kompilacji",
    "testowanie",
    "błąd testowania",
    "ok",
]

EXC_TIMEOUT=0.5
EXC_MEM_LIMIT=64*1024
EXC_OUT_LIMIT=2000


def wrap_err(text: str) -> str:
    return shorten(text, width=50, placeholder='...')