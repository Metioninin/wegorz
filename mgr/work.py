import logging
import multiprocessing
import tempfile
from functools import wraps
from pathlib import Path

from psycopg import Connection

from mgr.db import set_message, set_status
from mgr.exec import CppExecutor, ExecutionError, PythonExecutor, compile_cpp
from mgr.helpers import EXC_TIMEOUT, EXC_MEM_LIMIT, Simulator, Subm

logger = logging.getLogger("MGR")


def close_connection(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        finally:
            conn = args[1]
            try:
                conn.close()
            except Exception:
                logger.error("Failed to close connection for worker.")

    return wrapper


@close_connection
def work(subm: Subm, sim: Simulator, conn: Connection):
    box_id = int(multiprocessing.current_process().name.split("-")[1])

    exc_file = tempfile.NamedTemporaryFile()
    exc_path = Path(exc_file.name)

    if subm.lang == "CPP":
        try:
            set_status(subm.id, "kompilacja", conn)
            compile_cpp(subm.code, exc_path, box_id)
        except Exception as e:
            if not isinstance(e, ExecutionError):
                logger.error(f"During compilation of {subm.id} got error:\n{e}")
            set_status(subm.id, "błąd kompilacji", conn)
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
