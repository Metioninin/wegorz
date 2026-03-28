import json
from pathlib import Path

from mgr.sims.helpers import PrisonMove, Prisoner

Ranking = list[tuple[str, float]]


def calc_ranking(
    ranking: Ranking, gain1: float, gain2: float, players: tuple[Prisoner, Prisoner]
) -> None:
    for i in range(len(ranking)):
        if ranking[i][0] == players[0].username:
            ranking[i] = (ranking[i][0], ranking[i][1] + gain1)
        elif ranking[i][0] == players[1].username:
            ranking[i] = (ranking[i][0], ranking[i][1] + gain2)
    ranking.sort(key=lambda x: x[1], reverse=False)


def generate_notation(
    name1: str,
    name2: str,
    move1: PrisonMove | None,
    move2: PrisonMove | None,
    gain1: float,
    gain2: float,
    ranking: Ranking,
) -> str:
    
    realMove1 = 0
    realMove2 = 0
    if move1 == PrisonMove.BETRAY:
        realMove1 = 1
    elif move1 == None:
        realMove1 = 2
    if move2 == PrisonMove.BETRAY:
        realMove2 = 1
    elif move2 == None:
        realMove2 = 2
    notation_data = {
        "name1": name1,
        "name2": name2,
        "move1": realMove1,
        "move2": realMove2,
        "gain1": gain1,
        "gain2": gain2,
        "ranking": [],
    }

    for name, score in ranking:
        notation_data["ranking"].append({"name": name, "points": float(score)})

    return notation_data


GAINS = {
    (None, None): (10, 10),
    (None, PrisonMove.COOPERATE): (10, 0),
    (None, PrisonMove.BETRAY): (10, 0),
    (PrisonMove.COOPERATE, None): (0, 10),
    (PrisonMove.BETRAY, None): (0, 10),
    (PrisonMove.COOPERATE, PrisonMove.COOPERATE): (4, 4),
    (PrisonMove.BETRAY, PrisonMove.BETRAY): (8, 8),
    (PrisonMove.BETRAY, PrisonMove.COOPERATE): (0, 10),
    (PrisonMove.COOPERATE, PrisonMove.BETRAY): (10, 0),
}


def _simulate(
    players: tuple[Prisoner, Prisoner],
    ranking: list[tuple[str, float]],
    test_mode: bool,
) -> str:
    move1 = players[0].get_move(raise_errors=test_mode)
    move2 = players[1].get_move(raise_errors=test_mode)

    gain1, gain2 = GAINS[(move1, move2)]

    calc_ranking(ranking, gain1, gain2, players)

    return generate_notation(
        players[0].username,
        players[1].username,
        move1,
        move2,
        gain1,
        gain2,
        ranking,
    )


def simulate(
    players: tuple[Prisoner, Prisoner],
    ranking: Ranking | None = None
) -> None:
    "If save_path not proviede then it can raise TestError"

    test_mode=save_path is None

    # give start info to players
    for player_id in range(2):
        enemy = players[1 - player_id]
        players[player_id].send_start_info(enemy.username)

    # create dummy ranking for solution testing
    if ranking is None:
        assert test_mode
        ranking = []

    # simulate
    return _simulate(players, ranking, test_mode)