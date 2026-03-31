import math
import random

from mgr.sims.helpers import LAZY_CONV, AgarioCode, Pair, PlayerInfoAgario

Ranking = list[tuple[str, int]]
FramePos = list[list[tuple[int, int]]]


def generate_notation(
    k: int,
    playerNames: list[str],
    framesTop: FramePos,
    framesBottom: FramePos,
    zone: list[int],
    ranking: Ranking,
) -> dict:
    notation_data = {
        "k": k,
        "playerNames": playerNames,
        "framesTop": [],
        "framesBottom": [],
        "zone": zone,
        "ranking": [],
    }

    for frame in framesTop:
        moves = [{"x": float(p[0]), "y": float(p[1])} for p in frame]
        notation_data["framesTop"].append({"moves": moves})

    for frame in framesBottom:
        moves = [{"x": float(p[0]), "y": float(p[1])} for p in frame]
        notation_data["framesBottom"].append({"moves": moves})

    for name, score in ranking:
        notation_data["ranking"].append({"name": name, "points": float(score)})

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
) -> Ranking:
    for i in range(len(results)):
        for j in range(len(curr_ranking)):
            if curr_ranking[j][0] == results[i][0]:
                name, score = curr_ranking[j]
                points = results[i][1] * POINTS_MULT
                curr_ranking[j] = (name, score + points)
                break

    curr_ranking.sort(key=lambda x: x[1], reverse=True)
    return curr_ranking


def moja_pierwsza_funkcja(pls: int, n: int, m: int) -> list[tuple[int, int]]:
    s: set[tuple[int, int]] = set()

    while len(s) != pls:
        s.add((random.randint(0, m - 1), random.randint(1, n)))

    d = list(s)
    random.shuffle(d)

    return d


def _simulate(
    players: list[AgarioCode], ranking: list[tuple[str, int]], raise_errors: bool
) -> dict:
    odw = []
    visited_indeces = []

    # notation variables
    deadNotation: list[tuple[str, int]] = []  # w kolejnosci rankingu
    playerNames: list[str] = [p.username for p in players]

    framesTopNotation: FramePos = []
    framesBottomNotation: FramePos = []

    zoneNotation: list[int] = []
    rankingNotation: Ranking = []

    players_count = lambda: len(players)

    k = math.ceil(
        math.sqrt(players_count() / (ST_A * ST_B * DENSITY))
    )  # 6k^2(ilosc pol[n*m])=ilosc_graczy/denisty
    n = ST_A * k
    m = ST_B * k

    initialIndex = {}
    initialPlayerCount = players_count()

    pposes = moja_pierwsza_funkcja(players_count(), n, m)

    # poczatkowe rozstawienie graczy na mapie
    for i, pp in zip(range(players_count()), pposes, strict=True):
        players[i].top = Pair(pp[0], pp[1])
        players[i].bot = players[i].top + Pair(1, -1)
        initialIndex[players[i].username] = i

    zoneFrequency = 10
    zone = 0

    def add_frame():
        framesTopNotation.append([(-1, -1) for _ in range(initialPlayerCount)])
        framesBottomNotation.append([(-1, -1) for _ in range(initialPlayerCount)])

        for i in range(players_count()):
            framesTopNotation[-1][initialIndex[players[i].username]] = (
                players[i].top.x,
                players[i].top.y,
            )
            framesBottomNotation[-1][initialIndex[players[i].username]] = (
                players[i].bot.x,
                players[i].bot.y,
            )
        zoneNotation.append(zone)

    # add start frame
    add_frame()

    while players_count() > 1:  # dopoki zyje co najmniej 2
        place = 1 + len(deadNotation)

        # listy pozycji wszystkich graczy (przed ruchami)
        others_t = []
        others_b = []
        for i in range(players_count()):
            others_t.append(players[i].top)
            others_b.append(players[i].bot)

        newMoves = []
        for i in range(players_count()):
            # i-ty gracz musi byc pierwszy
            others_t[0], others_t[i] = others_t[i], others_t[0]
            others_b[0], others_b[i] = others_b[i], others_b[0]

            info = PlayerInfoAgario(n, m, zone, others_t, others_b)
            move = players[i].get_move(info, raise_errors)
            newMoves.append(move)  # zapisz na pozniej jaki ruch zrobil gracz i

            others_t[0], others_t[i] = others_t[i], others_t[0]
            others_b[0], others_b[i] = others_b[i], others_b[0]

        i = 0
        while i < players_count():
            if newMoves[i] is None:
                deadNotation.append((players[i].username, place))
                players.pop(i)
                newMoves.pop(i)
                continue

            # rekonstrukcja ruchow i aktualizacja pozycji
            players[i].top += LAZY_CONV[newMoves[i]]
            players[i].bot += LAZY_CONV[newMoves[i]]
            i += 1

        # zapisuje aktualna pozycje
        add_frame()

        odw = [False] * players_count()
        newPositions = [0] * players_count()

        # sprawdzenie konfliktów
        for i in range(players_count()):
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
        while i < players_count():  # realizacja zwiekszania/usuwania
            while newPositions[i] == -1:
                newPositions.pop(i)
                deadNotation.append((players[i].username, place))
                players.pop(i).kill(len(deadNotation), raise_errors)

                if i >= players_count():
                    break
            if i >= players_count():
                break

            if newPositions[i] == 0:
                i += 1
                continue

            players[i].bot = Pair(
                players[i].top.x + newPositions[i], players[i].top.y - newPositions[i]
            )
            i += 1

        # co iles klatek zone sie zmniejsza
        if len(zoneNotation) % zoneFrequency == 0:
            zone += 1

        # gdy gracz w strefie odejmij mu miejsce i jak jest za maly to go usun
        i = 0
        while i < players_count():
            if (
                players[i].top.x < zone
                or players[i].top.y > n - zone
                or players[i].bot.x > m - zone
                or players[i].bot.y < zone
            ):
                players[i].bot += Pair(-1, 1)

                if players[i].top == players[i].bot:
                    deadNotation.append((players[i].username, place))
                    players.pop(i).kill(len(deadNotation), raise_errors)
            i += 1

    # add last frame
    add_frame()

    if len(players):
        deadNotation.append((players[0].username, 1 + len(deadNotation)))
    deadNotation.reverse()

    newRanking = calc_ranking(ranking, deadNotation)

    for i in range(len(newRanking)):
        rankingNotation.append(newRanking[i])

    return generate_notation(
        k,
        playerNames,
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
