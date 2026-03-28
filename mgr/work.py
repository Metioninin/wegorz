import logging
import multiprocessing
import tempfile
import traceback
from pathlib import Path

from mgr.db import get_conn, set_message, set_status
from mgr.exec import CppExecutor, ExecutionError, PythonExecutor, compile_cpp
from mgr.helpers import EXC_MEM_LIMIT, EXC_TIMEOUT, Subm
from mgr.sims.helpers import FakePoker, FakePrisoner, PokerCode, Prisoner, TestError
from mgr.sims.prison import simulate as simulate_prison
from mgr.sims.simPoker import simulate as simulate_poker

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

    match round_id:
        case 1:
            start_exc()
            simulate_prison(players=(Prisoner("0", exc), FakePrisoner()), match_id=1)
            stop_exc()
        case 2:
            start_exc()
            simulate_poker(players=[PokerCode("0", exc), FakePoker()], match_id=1)
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
