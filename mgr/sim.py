from dataclasses import dataclass
from typing import Any
from code import Code, Move
import math
import random

@dataclass
class PlayerInfo:
    n: int
    m: int
    zone: int


st_a = 2
st_b = 3
density = 0.1 #between  (0, 1>

def simulate(players: list[Code]) -> dict[str, Any]:
    #players[i].get_move(cokolwiek) == Move.DOWN
    
    players_count = len(players);
    k = math.ceil(math.sqrt(players_count/(st_a*st_b*density)))
    n = st_a * k
    m = st_b * k
    for i in range(players_count):
        players[i].top_x = random.randint(0, m-1)
        players[i].bot_x = players[i].top_x + 1
        players[i].top_y = random.randint(1, n);
        players[i].bot_y = players[i].top_y - 1

    

    return {}

