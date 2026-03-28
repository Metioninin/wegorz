import logging
import multiprocessing
from random import shuffle
import tempfile
import traceback
from pathlib import Path

from mgr.db import get_conn, set_message, set_status
from mgr.exec import CppExecutor, ExecutionError, PythonExecutor, compile_cpp
from mgr.helpers import EXC_MEM_LIMIT, EXC_TIMEOUT, Subm, wrap_err
from mgr.sims.helpers import FakePoker, FakePrisoner, PokerCode, Prisoner, TestError, POKER_TESTS, AgarioCode, FakeAgario, AGARIO_TESTS
from mgr.sims.prison import simulate as simulate_prison
from mgr.sims.simPoker import simulate as simulate_poker
from mgr.sims.agario import simulate as simulate_agario

logger = logging.getLogger("MGR")


def run_simulator(
    round_id: int, exc: CppExecutor | PythonExecutor, exc_path: Path
) -> None:
    def start_exc():
        exc.start_isolation()
        exc.setup_sandbox(exc_path)
        exc.run()

    def stop_exc():
        exc.exit()

    def format_test_err(e: TestError, nr: int, cnt: int, test: str | None = None):
        e.args = (f"Test {nr}/{cnt}:\n{e.args[0]}",) + e.args[1:]

        if test:
            e.args = (f"{e.args[0]}\n\nKomunikacja:\n{test}",) + e.args[1:]
        
    match round_id:
        case 1:
            start_exc()
            
            try:
                simulate_prison(players=(Prisoner("0", exc), FakePrisoner()), match_id=1)
            except TestError as e:
                format_test_err(e, nr=1, cnt=1)
                raise

            stop_exc()
        case 2:
            for idx, test in enumerate(POKER_TESTS, start=1):
                start_exc()

                players = [PokerCode("0", exc, trace=True)] + [FakePoker() for _ in range(5)]
                shuffle(players)
                pidx = next(i for i, p in enumerate(players) if type(p) is PokerCode)

                try:
                    simulate_poker(players, money=test, match_id=1)
                except TestError as e:
                    format_test_err(e, idx, len(POKER_TESTS), test="\n".join(players[pidx]._comm))
                    raise

                stop_exc()
        case 3:
            for j in range(3):
                start_exc()

                players = [AgarioCode("A", exc, trace=True)] + [FakeAgario() for _ in range(5)]
                shuffle(players)
                pidx = next(i for i, p in enumerate(players) if type(p) is AgarioCode)

                try:
                    simulate_agario(players)
                except TestError as e:
                    format_test_err(e, idx, len(POKER_TESTS), test="\n".join(players[pidx]._comm))
                    raise

                stop_exc()
        case _:
            raise NotImplementedError()


def work(subm: Subm):
    with get_conn() as conn:
        box_id = int(multiprocessing.current_process().name.split("-")[1])

        with tempfile.NamedTemporaryFile() as exc_file:
            exc_path = Path(exc_file.name)

            if subm.lang == "CPP":
                try:
                    set_status(subm.id, "kompilacja", conn)
                    compile_cpp(subm.code, exc_path, box_id)
                except Exception as e:
                    set_status(subm.id, "błąd kompilacji", conn)

                    if not isinstance(e, ExecutionError):
                        logger.error(f"During compilation of {subm.id} got error:\n{e}")
                    else:
                        set_message(subm.id, str(e), conn)

                    return
            else:
                with open(exc_path, "w") as f:
                    f.write(subm.code)

            set_status(subm.id, "testowanie", conn)

            kwargs = {
                "box_id": box_id,
                "timeout": EXC_TIMEOUT,
                "mem_limit": EXC_MEM_LIMIT,
            }
            exc = (
                CppExecutor(**kwargs)
                if subm.lang == "CPP"
                else PythonExecutor(**kwargs)
            )

            try:
                run_simulator(subm.round_id, exc, exc_path)
            except Exception as e:
                set_status(subm.id, "błąd testowania", conn)

                if isinstance(e, TestError):
                    set_message(subm.id, str(e), conn)
                else:
                    logger.error(
                        f"Testing failed for submission {subm.id}.\n"
                        + f"{str(traceback.format_exc())}"
                    )
                    set_message(subm.id, "Błąd serwera :)", conn)
            else:
                set_status(subm.id, "ok", conn)
                set_message(subm.id, "Pomyślnie ukończono testy", conn)
            finally:
                exc.exit()
