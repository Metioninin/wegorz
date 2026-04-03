#
# Uwaga! Generate.py byl zmieninay na biezaco, wiec
# nie dziala on dla rund 1 i 2, a 3 idk
# 

from pathlib import Path
from random import shuffle
import tempfile
from dataclasses import dataclass
from typing import Any, Generator
import json

from psycopg.rows import DictRow, dict_row
from mgr.db import get_conn
from mgr.exec import CppExecutor, PythonExecutor, compile_cpp
from mgr.helpers import EXC_MEM_LIMIT, EXC_TIMEOUT

from mgr.sims.helpers import FakeAgario, FoldPoker, PokerCode, Prisoner, AgarioCode
from mgr.sims.prison import simulate as simulate_prison
from mgr.sims.simPoker import simulate as simulate_poker
from mgr.sims.agario import simulate as simulate_agario


@dataclass
class Code:
    code: str
    lang: str
    login: str


def get_subm(login: str, rnd: int) -> Code:
    conn = get_conn()

    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            WITH user_id AS (
                SELECT * FROM users WHERE login = %s
            )
            SELECT
                s.code,
                s.lang,
                u.login
            FROM submissions s
            JOIN user_id u ON true
            WHERE 
                s.user_id = u.id AND s.round_id = %s
                AND s.status IN ('ok', 'błąd testowania')
            ORDER BY
                CASE 
                    WHEN s.status = 'ok' THEN 1
                    WHEN s.status = 'błąd testowania' THEN 2
                END,
                s.send_at DESC
            """,
            (login, rnd),
        )
        res = cur.fetchone()

        if res is None:
            res = DictRow({"code": "", "lang": "PY", "login": login})

    return Code(**res)


def create_executor(
    box_id: int, code: str, lang: str
) -> tuple[tempfile._TemporaryFileWrapper, CppExecutor | PythonExecutor]:
    exc_file = tempfile.NamedTemporaryFile()
    exc_path = Path(exc_file.name)

    if lang == "CPP":
        compile_cpp(code, exc_path, box_id)
    else:
        with open(exc_path, "w") as f:
            f.write(code)

    kwargs = {
        "box_id": box_id,
        "timeout": EXC_TIMEOUT,
        "mem_limit": EXC_MEM_LIMIT,
    }
    return (
        exc_file,
        CppExecutor(**kwargs) if lang == "CPP" else PythonExecutor(**kwargs),
    )


def run_match(
    rnd: int,
    ranking: Any,
    execs: list[tuple[str, PythonExecutor | CppExecutor]],
    group_id: int,
) -> dict:
    assert len(execs) > 0

    def get_botname() -> Generator[str, None, None]:
        val = 0

        while True:
            val += 1
            yield f"bot{val}"

    gen = get_botname()

    match rnd:
        case 1:
            assert len(execs) == 2
            players = (Prisoner(*execs[0]), Prisoner(*execs[1]))
            return simulate_prison(players, ranking, test_mode=False)
        case 3:
            assert len(execs)
            assert len(execs) <= 6

            players = [PokerCode(login, exc) for login, exc in execs]

            while len(players) < 6:
                players.append(FoldPoker(next(gen), None))

            res = simulate_poker(players, ranking, test_mode=False)
            res["group"] = str(group_id)
            
            return res
        case 2:
            assert len(execs)
            assert len(execs) <= 6

            players = [AgarioCode(login, exc) for login, exc in execs]

            while len(players) < 6:
                players.append(FakeAgario(username=next(gen), exc=None))

            shuffle(players)

            res = simulate_agario(players, ranking, test_mode=False)
            res["group"] = str(group_id)

            return res
        case _:
            raise Exception("pojebalo cie")


def get_logins(rid: int) -> list[str]:
    conn = get_conn()

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT u.login
            FROM submissions s
            JOIN users u ON u.id = s.user_id
            WHERE 
                s.round_id = %s 
                AND s.status = 'ok'
                AND u.login != '317'
            ORDER BY u.login
            """,
            (rid,),
        )
        res = cur.fetchall()

    return [row[0] for row in res]


def ceil_div(x, y):
    return (x + y - 1) // y


def gen_groups(players: list[str], group_cnt: int) -> list[list[str]]:
    shuffle(players)

    base_size = len(players) // group_cnt + 1
    groups_cnt = ceil_div(len(players), base_size)

    groups: list[list[str]] = []

    for i in range(groups_cnt):
        start = i * base_size
        end = start + base_size
        groups.append(players[start:end])

    return groups


def gen_matches(group: list[str], times: int) -> list[list[str]]:
    return [group for _ in range(times)]


if __name__ == "__main__":
    print("KURWA! UPEWNIJ SIE ZE NIE ROBISZ TEGO W VPSie!", flush=True)
    print(
        "PG_DUMPUJE BASE Z VPSA, napraw i odpal wegorza u siebie!",
        flush=True,
    )

    rnd = 3
    assert rnd

    group_cnt = 1
    assert group_cnt

    groups = gen_groups(get_logins(rnd), group_cnt)
    print(groups, flush=True)
    shuffle(groups[0])
    data = []

    for gidx, group in enumerate(groups, start=1):
        times = 3
        assert times

        matches: list[list[str]] = gen_matches(group, times)
        assert matches
        
        ranking = [(p, 1000) for p in group] # TODO: stawka

        for midx, match in enumerate(matches):
            print(midx, len(matches), flush=True)
            execs: list[tuple[str, CppExecutor | PythonExecutor]] = []

            for idx, player in enumerate(match):
                subm = get_subm(player, rnd)
                exc_path, exc = create_executor(
                    box_id=idx, code=subm.code, lang=subm.lang
                )

                execs.append((player, exc))

                exc.start_isolation()
                exc.setup_sandbox(Path(exc_path.name))
                exc.run()

            data.append(run_match(rnd, ranking, execs, gidx))

            for exc in execs:
                exc[1].exit()

    match_path = Path("/matches")
    match_path.mkdir(exist_ok=True)
    save_path = match_path / "match.json"

    tasiemiec = json.dumps({"data": data}, indent=4, ensure_ascii=False)
    save_path.write_text(tasiemiec, encoding="utf-8")
