import logging
import signal
import sys
from multiprocessing import Pool, cpu_count
from time import sleep

from mgr.db import get_conn, get_unprocessed_subm, set_status
from mgr.helpers import Simulator
from mgr.work import work


# setup signal
def handle_sigint(signum, frame):
    print("Exiting...")
    sys.exit(0)


signal.signal(signal.SIGINT, handle_sigint)
signal.signal(signal.SIGTERM, handle_sigint)

# setup logging
logger = logging.getLogger("MGR")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s")
)
logger.addHandler(handler)


work_pool = Pool(processes=cpu_count())

logger.info("Started.")

while True:
    conn = get_conn()
    subm = get_unprocessed_subm(conn)

    if subm is None:
        conn.close()
        sleep(2)
        continue

    logger.info(f"Received submission {subm.id}")

    # NOTE: after the crash it is advised to 
    #       set all subms with similiar statuses to 'oczekiwanie'
    subm_status = "testowanie" if subm.lang == "PY" else "kompilacja"
    set_status(subm.id, status=subm_status, conn=conn)

    work_pool.apply(func=work, args=(subm, Simulator(), conn))
