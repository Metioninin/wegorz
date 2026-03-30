import math
import random

from mgr.sims.helpers import LAZY_CONV, AgarioCode, AgarioMove, Pair, PlayerInfoAgario

Ranking = list[tuple[str, int]]


def generate_notation(
    k: int,
    playerNames: list[str],
    framesTop: list,
    framesBottom: list,
    zone: list,
    ranking: Ranking,
) -> dict:
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

    return notation_data


def intersect(a: AgarioCode, b: AgarioCode) -> bool:
    return not (
        a.bot.x <= b.top.x
        or a.top.x >= b.bot.x
        or a.bot.y >= b.top.y
        or a.top.y <= b.bot.y
    )


POINTS_MULT = 5
ST_A = 2
ST_B = 3
DENSITY = 0.1  # between  (0, 1>


def dfs(
    players: list[AgarioCode], visited_indeces: list[int], odw: list[bool], me: int
) -> None:
    visited_indeces.append(me)
    odw[me] = True

    for i in range(len(players)):
        if i == me or not intersect(players[i], players[me]) or odw[i]:
            continue
        dfs(players, visited_indeces, odw, i)


def calc_ranking(
    curr_ranking: list[tuple[str, int]],
    results: list[tuple[str, int]],
    overwrite: list[tuple[str, int]],
) -> Ranking:
    for i in range(len(results)):
        for j in range(len(curr_ranking)):
            if curr_ranking[j][0] == results[i]:
                name, score = curr_ranking[j]
                points = results[i][1] * POINTS_MULT
                overwrite.append((results[i][0], points))
                curr_ranking[j] = (name, score + points)
                break

    curr_ranking.sort(key=lambda x: x[1], reverse=True)
    return curr_ranking


def _simulate(
    players: list[AgarioCode], ranking: list[tuple[str, int]], raise_errors: bool
) -> dict:
    odw = []
    visited_indeces = []

    # notation variables
    playerNamesNotation: list[tuple[str, int]] = []  # w kolejnosci rankingu
    framesTopNotation = []
    framesBottomNotation = []
    zoneNotation = []
    rankingNotation = []

    players_count = len(players)

    k = math.ceil(
        math.sqrt(players_count / (ST_A * ST_B * DENSITY))
    )  # 6k^2(ilosc pol[n*m])=ilosc_graczy/denisty
    n = ST_A * k
    m = ST_B * k

    initialIndex = {}
    initialPlayerCount = players_count

    for i in range(players_count):  # poczatkowe rozstawienie graczy na mapie
        players[i].top = Pair(random.randint(0, m - 1), random.randint(1, n))
        players[i].bot = players[i].top + Pair(1, -1)
        initialIndex[players[i].username] = i

    zoneFrequency = 10
    zoneCurr = 0
    zone = 0

    while players_count > 1:  # dopoki zyje co najmniej 2
        place = 1 + len(playerNamesNotation)

        # zapisuje aktualna pozycje
        framesTopNotation.append([Pair(-1, -1) for _ in range(initialPlayerCount)])
        framesBottomNotation.append([Pair(-1, -1) for _ in range(initialPlayerCount)])

        for i in range(players_count):
            framesTopNotation[zoneCurr][initialIndex[players[i].username]] = Pair(
                players[i].top.x, players[i].top.y
            )
            framesBottomNotation[zoneCurr][initialIndex[players[i].username]] = Pair(
                players[i].bot.x, players[i].bot.y
            )
        zoneNotation.append(zone)

        # listy pozycji wszystkich graczy (przed ruchami)
        others_t = []
        others_b = []
        for i in range(players_count):
            others_t.append(players[i].top)
            others_b.append(players[i].bot)

        newMoves = []
        for i in range(players_count):
            # i-ty gracz musi byc pierwszy
            others_t[0], others_t[i] = others_t[i], others_t[0]
            others_b[0], others_b[i] = others_b[i], others_b[0]

            info = PlayerInfoAgario(n, m, zone, others_t, others_b)
            move = players[i].get_move(info, raise_errors)
            newMoves.append(move)  # zapisz na pozniej jaki ruch zrobil gracz i

            others_t[0], others_t[i] = others_t[i], others_t[0]
            others_b[0], others_b[i] = others_b[i], others_b[0]

        i = 0
        while i < players_count:
            if newMoves[i] is None:
                playerNamesNotation.append((players[i].username, place))
                players.pop(i)
                newMoves.pop(i)
                players_count -= 1
                continue

            # rekonstrukcja ruchow i aktualizacja pozycji
            players[i].top += LAZY_CONV[newMoves[i]]
            players[i].bot += LAZY_CONV[newMoves[i]]
            i += 1

        odw = [False] * players_count
        newPositions = [0] * players_count

        for i in range(players_count):
            if not odw[i]:
                visited_indeces = []
                dfs(players, visited_indeces, odw, i)

            if len(visited_indeces) > 1:  # mamy bitke
                sqSum = 0
                for j in range(len(visited_indeces)):
                    sqSum += (
                        players[visited_indeces[j]].top.y
                        - players[visited_indeces[j]].bot.y
                    ) ** 2

                # losowanie zwyciezcy walki pod katem wielkosci
                los = random.randint(1, sqSum)

                currSum = 0
                for j in range(len(visited_indeces)):
                    currSum += (
                        players[visited_indeces[j]].top.y
                        - players[visited_indeces[j]].bot.y
                    ) ** 2

                    if currSum >= los:  # j to zwyciezca
                        newPositions[visited_indeces[j]] = math.ceil(math.sqrt(sqSum))

                        for ll in range(len(visited_indeces)):  # przegranych usuwamy
                            if ll == j:
                                continue
                            newPositions[visited_indeces[ll]] = -1
                        break
        i = 0
        while i < players_count:  # realizacja zwiekszania/usuwania
            while newPositions[i] == -1:
                newPositions.pop(i)
                playerNamesNotation.append((players[i].username, place))
                players_count -= 1
                dead = players.pop(i)
                dead.kill(len(playerNamesNotation), raise_errors)

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

        # co iles klatek zone sie zmniejsza
        zoneCurr += 1
        if zoneCurr % zoneFrequency == 0:
            zone += 1

        # gdy gracz w strefie odejmij mu miejsce i jak jest za maly to go usun
        i = 0
        while i < players_count:
            while (
                players[i].top.x < zone
                or players[i].top.y > n - zone
                or players[i].bot.x > m - zone
                or players[i].bot.y < zone
            ):
                players[i].bot += Pair(-1, 1)
                if players[i].top == players[i].bot:
                    playerNamesNotation.append((players[i].username, place))
                    players_count -= 1
                    dead = players.pop(i)
                    dead.kill(len(playerNamesNotation), raise_errors)

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

    if len(players):
        playerNamesNotation.append((players[0].username, 1 + len(playerNamesNotation)))
    playerNamesNotation.reverse()

    playerNamesNotationReal = []
    newRanking = calc_ranking(ranking, playerNamesNotation, playerNamesNotationReal)

    for i in range(len(newRanking)):
        rankingNotation.append(newRanking[i])

    return generate_notation(
        k,
        playerNamesNotationReal,
        framesTopNotation,
        framesBottomNotation,
        zoneNotation,
        newRanking,
    )


def simulate(
    players: list[AgarioCode], ranking: Ranking | None = None, test_mode: bool = True
) -> dict:
    if ranking is None:
        assert test_mode
        ranking = [(p.username, 0) for p in players]
    return _simulate(players, ranking, raise_errors=test_mode)
