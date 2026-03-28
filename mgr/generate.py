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

from mgr.sims.helpers import FoldPoker, PokerCode, Prisoner, AgarioCode
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
            (login,rnd),
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
        case 2:
            assert len(execs) <= 6

            players = [PokerCode(login, exc) for login, exc in execs]

            while len(players) < 6:
                players.append(FoldPoker(next(gen), None))

            shuffle(players)

            return simulate_poker(players, ranking, test_mode=False)
        case 3:
            assert len(execs) <= 6

            players = [AgarioCode(login, exc) for login, exc in execs]
            shuffle(players)
            return simulate_agario(players, ranking)


if __name__ == "__main__":
    print("KURWA! UPEWNIJ SIE ZE NIE ROBISZ TEGO W VPSie!", flush=True)
    print(
        "POBIERZ DB ZE VPSA (czyli caly folder .db-data) i odpal wegorza u siebie!",
        flush=True,
    )

    rnd = -1  # TODO:
    assert rnd != -1

    matches: list[list[str]] = []  # TODO: loginy ludzi
    ranking = []  # TODO: set depending on game
    assert matches

    Path("/matches").mkdir(exist_ok=True)
    save_path = Path(f"/matches/match.json")
    data = []
    for midx, match in enumerate(matches):
        execs: list[tuple[str, CppExecutor | PythonExecutor]] = []

        for idx, player in enumerate(match):
            subm = get_subm(player, rnd)
            exc_path, exc = create_executor(box_id=idx, code=subm.code, lang=subm.lang)

            execs.append((player, exc))

            exc.start_isolation()
            exc.setup_sandbox(Path(exc_path.name))
            exc.run()

        data.append(run_match(rnd, ranking, execs))

        for exc in execs:
            exc[1].exit()
    tasiemiec = json.dumps(data, indent=4, ensure_ascii=False)
    save_path.write_text(tasiemiec, encoding='utf-8')