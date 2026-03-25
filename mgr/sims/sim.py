import json
import math
import random
from dataclasses import dataclass

from mgr.sims.subm import Code, Pair


def generate_notation(k, playerNames, framesTop, framesBottom, zone, ranking):
    notation_data = {
        "k": k,
        "playerNames": [],
        "framesTop": [],
        "framesBottom": [],
        "zone": zone,
        "ranking": [],
    }

    for name, score in playerNames:
        notation_data["playerNames"].append(
            {"order": {"name": name, "points": float(score)}}
        )

    for frame in framesTop:
        moves = [{"x": float(p.x), "y": float(p.y)} for p in frame]
        notation_data["framesTop"].append({"moves": moves})

    for frame in framesBottom:
        moves = [{"x": float(p.x), "y": float(p.y)} for p in frame]
        notation_data["framesBottom"].append({"moves": moves})

    for name, score in ranking:
        notation_data["ranking"].append(
            {"order": {"name": name, "points": float(score)}}
        )

    return json.dumps(notation_data, indent=4, ensure_ascii=False)

    with open("notka.json", "w", encoding="utf-8") as f:
        json.dump(notation_data, f, indent=4, ensure_ascii=False)
    return {}


@dataclass
class PlayerInfo:
    n: int
    m: int
    zone: int
    top: list[Pair]
    bot: list[Pair]


def intersect(topa: Pair, bota: Pair, topb: Pair, botb: Pair) -> bool:
    return not (
        bota.x <= topb.x or topa.x >= botb.x or bota.y >= topb.y or topa.y <= botb.y
    )


pointsMult = 5
st_a = 2
st_b = 3
density = 0.1  # between  (0, 1>
odw = []
visited_indeces = []


def dfs(players: list[Code], me: int):
    visited_indeces.append(me)
    odw[me] = True
    for i in range(len(players)):
        if (
            i == me
            or not intersect(
                players[i].top, players[i].bot, players[me].top, players[me].bot
            )
            or odw[i]
        ):
            continue
        dfs(players, i)


def calc_ranking(
    curr_ranking: list[tuple[str, float]],
    results: list[str],
    overwrite: list[tuple[str, float]],
):
    for i in range(len(results)):
        for j in range(len(curr_ranking)):
            if curr_ranking[j][0] == results[i]:
                name, score = curr_ranking[j]
                points = (len(results) - i) * pointsMult
                overwrite.append((results[i], points))
                curr_ranking[j] = (name, score + points)
                break
    curr_ranking.sort(key=lambda x: x[1], reverse=True)
    return curr_ranking


def simulate(players: list[Code], ranking: list[tuple[str, float]]):
    # notation variables
    playerNamesNotation = []  # w kolejnosci rankingu
    framesTopNotation = []
    framesBottomNotation = []
    zoneNotation = []
    rankingNotation = []

    global odw
    global visited_indeces
    players_count = len(players)
    k = math.ceil(
        math.sqrt(players_count / (st_a * st_b * density))
    )  # 6k^2(ilosc pol[n*m])=ilosc_graczy/denisty
    n = st_a * k
    m = st_b * k
    initialIndex = {}
    initialPlayerCount = players_count
    for i in range(players_count):  # poczatkowe rozstawienie graczy na mapie
        players[i].top = Pair(random.randint(0, m - 1), random.randint(1, n))
        players[i].bot = players[i].top + Pair(1, -1)
        initialIndex[players[i].username] = i
    zoneFrequency = 10
    zoneCurr = 0

    print(str(n) + " " + str(m))
    for i in range(players_count):
        print(
            players[i].username
            + " "
            + str(players[i].top.x)
            + " "
            + str(players[i].top.y)
            + " "
            + str(players[i].bot.x)
            + " "
            + str(players[i].bot.y)
        )

    zone = 0
    while players_count > 1:  # dopoki zyje co najmniej 2
        # zapisuje aktualna pozycje
        framesTopNotation.append([Pair(-1, -1)] * initialPlayerCount)
        framesBottomNotation.append([Pair(-1, -1)] * initialPlayerCount)
        for i in range(players_count):
            framesTopNotation[zoneCurr][initialIndex[players[i].username]] = Pair(
                players[i].top.x, players[i].top.y
            )
            framesBottomNotation[zoneCurr][initialIndex[players[i].username]] = Pair(
                players[i].bot.x, players[i].bot.y
            )
        zoneNotation.append(zone)

        others_t = []  # listy pozycji wszystkich graczy (przed ruchami)
        others_b = []
        newMoves = []
        for i in range(players_count):
            others_t.append(players[i].top)
            others_b.append(players[i].bot)
        for i in range(players_count):
            others_t[0], others_t[i] = (
                others_t[i],
                others_t[0],
            )  # i-ty gracz musi byc pierwszy
            others_b[0], others_b[i] = others_b[i], others_b[0]

            info = PlayerInfo(n, m, zone, others_t, others_b)
            move = players[i].get_move(info)
            print(players[i].username + " rusza sie " + str(move))
            newMoves.append(move)  # zapisz na pozniej jaki ruch zrobil gracz i

            others_t[0], others_t[i] = others_t[i], others_t[0]
            others_b[0], others_b[i] = others_b[i], others_b[0]

        for i in range(players_count):
            players[i].top += newMoves[
                i
            ].value  # rekonstrukcja ruchow i aktualizacja pozycji
            players[i].bot += newMoves[i].value

        odw = [False] * players_count
        newPositions = [0] * players_count
        for i in range(players_count):
            if not odw[i]:
                visited_indeces = []
                dfs(players, i)
            if len(visited_indeces) > 1:  # mamy bitke
                sqSum = 0
                for j in range(len(visited_indeces)):
                    sqSum += (
                        players[visited_indeces[j]].top.y
                        - players[visited_indeces[j]].bot.y
                    ) * (
                        players[visited_indeces[j]].top.y
                        - players[visited_indeces[j]].bot.y
                    )
                los = random.randint(
                    1, sqSum
                )  # losowanie zwyciezcy walki pod katem wielkosci
                currSum = 0
                for j in range(len(visited_indeces)):
                    currSum += (
                        players[visited_indeces[j]].top.y
                        - players[visited_indeces[j]].bot.y
                    ) * (
                        players[visited_indeces[j]].top.y
                        - players[visited_indeces[j]].bot.y
                    )
                    if currSum >= los:  # j to zwyciezca
                        newPositions[visited_indeces[j]] = math.ceil(math.sqrt(sqSum))
                        for l in range(len(visited_indeces)):  # przegranych usuwamy
                            if l == j:
                                continue
                            newPositions[visited_indeces[l]] = -1
                        break
        i = 0
        while i < players_count:  # realizacja zwiekszania/usuwania
            while newPositions[i] == -1:
                newPositions.pop(i)
                playerNamesNotation.append(players[i].username)
                players.pop(i)
                players_count -= 1
                if i >= players_count:
                    break
            if i >= players_count:
                break
            if newPositions[i] == 0:
                i += 1
                continue
            players[i].bot = Pair(
                players[i].top.x + newPositions[i], players[i].top.y - newPositions[i]
            )
            i += 1

        zoneCurr += 1  # co iles klatek zone sie zmniejsza
        if zoneCurr % zoneFrequency == 0:
            zone += 1
        i = 0
        while (
            i < players_count
        ):  # gdy gracz w strefie odejmij mu miejsce i jak jest za maly to go usun
            while (
                players[i].top.x < zone
                or players[i].top.y > n - zone
                or players[i].bot.x > m - zone
                or players[i].bot.y < zone
            ):
                players[i].bot += Pair(-1, 1)
                if players[i].top == players[i].bot:
                    playerNamesNotation.append(players[i].username)
                    players.pop(i)
                    players_count -= 1
                    if i >= players_count:
                        break
                else:
                    break
            i += 1

        framesTopNotation.append([Pair(-1, -1)] * initialPlayerCount)
        framesBottomNotation.append([Pair(-1, -1)] * initialPlayerCount)
        for i in range(players_count):
            framesTopNotation[zoneCurr][initialIndex[players[i].username]] = Pair(
                players[i].top.x, players[i].top.y
            )
            framesBottomNotation[zoneCurr][initialIndex[players[i].username]] = Pair(
                players[i].bot.x, players[i].bot.y
            )
        zoneNotation.append(zone)

        print("Koniec " + str(zoneCurr) + " klatki:")
        print(str(players_count) + " graczy")
        print(str(zone) + " zone")
        for i in range(players_count):
            print(
                players[i].username
                + " "
                + str(players[i].top.x)
                + " "
                + str(players[i].top.y)
                + " "
                + str(players[i].bot.x)
                + " "
                + str(players[i].bot.y)
            )

    playerNamesNotation.append(players[0].username)
    playerNamesNotation.reverse()
    playerNamesNotationReal = []
    newRanking = calc_ranking(ranking, playerNamesNotation, playerNamesNotationReal)
    for i in range(len(newRanking)):
        rankingNotation.append(newRanking[i])
    return (
        generate_notation(
            k,
            playerNamesNotationReal,
            framesTopNotation,
            framesBottomNotation,
            zoneNotation,
            newRanking,
        ),
        newRanking,
    )
