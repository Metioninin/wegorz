from dataclasses import dataclass
from typing import Any
from mgr.sims.subm import PrisonCode
import json

def calc_ranking(ranking: list[(str, float)], gain1, gain2, players: list[PrisonCode]):
    for i in range(len(ranking)):
        if ranking[i][0] == players[0].username:
            nowy = (ranking[i][0], ranking[i][1] + gain1)
            ranking[i] = nowy
        if ranking[i][0] == players[1].username:
            nowy = (ranking[i][0], ranking[i][1] + gain2)
            ranking[i] = nowy
    ranking.sort(key=lambda x: x[1], reverse=False)

def generate_notation(name1, name2, move1, move2, gain1, gain2, ranking):
    notation_data = {
        "name1": name1,
        "name2": name2,
        "move1": move1,
        "move2": move2,
        "gain1": gain1,
        "gain2": gain2,
        "ranking": []
    }

    for name, score in ranking:
        notation_data["ranking"].append({
            "name": name,
            "points": float(score)
        })

    return json.dumps(notation_data, indent=4, ensure_ascii=False)

    with open("notka.json", 'w', encoding='utf-8') as f:
        json.dump(notation_data, f, indent=4, ensure_ascii=False)
    return {}

def simulate(players: list[PrisonCode], ranking: list[(str, float)]):
    move1 = players[0].get_move(players[1].username)
    move2 = players[1].get_move(players[0].username)
    gain1 = 0
    gain2 = 0
    if move1 == 'Wspolpraca' and move2 == 'Wspolpraca':
        gain1 = 1
        gain2 = 1
    elif move1 == 'Wspolpraca' and move2 == 'Niezgoda':
        gain1 = 10
        gain2 = 0
    elif move1 == 'Niezgoda' and move2 == 'Wspolpraca':
        gain1 = 0
        gain2 = 10
    else:
        gain1 = 5
        gain2 = 5

    calc_ranking(ranking, gain1, gain2, players)
    move11 = 0
    move22 = 0
    if move1 == 'Niezgoda':
        move11 = 1
    if move2 == 'Niezgoda':
        move22 = 1
    return (generate_notation(players[0].username, players[1].username, move11, move22, gain1, gain2, ranking), ranking)