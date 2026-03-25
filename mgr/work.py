import logging
import multiprocessing
import tempfile
from pathlib import Path

from mgr.db import get_conn, set_message, set_status
from mgr.exec import CppExecutor, ExecutionError, PythonExecutor, compile_cpp
from mgr.helpers import EXC_TIMEOUT, EXC_MEM_LIMIT, Simulator, Subm

logger = logging.getLogger("MGR")


def work(subm: Subm, sim: Simulator):
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

            set_status(subm.id, "testowanie", conn)

            kwargs = {"box_id": box_id, "timeout": EXC_TIMEOUT, "mem_limit": EXC_MEM_LIMIT}

            exc = CppExecutor(**kwargs) if subm.lang == "CPP" else PythonExecutor(**kwargs)

            exc.start_isolation()
            exc.setup_sandbox(exc_path)
            exc.run()

            try:
                sim.test(exc)
            except Exception as e:
                set_status(subm.id, "błąd testowania", conn)

                if isinstance(e, ExecutionError):
                    set_message(subm.id, str(e), conn)
                else:
                    logger.error(f"Testing failed for submission {subm.id}.\n{e}")
                    set_message(subm.id, "Błąd serwera :)", conn)
            else:
                set_status(subm.id, "gotowy", conn)
            finally:
                exc.exit()
