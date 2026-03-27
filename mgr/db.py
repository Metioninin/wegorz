import logging
import os

from psycopg import Connection
from psycopg.rows import dict_row
from retry import retry

from mgr.helpers import Status, Subm


logger = logging.getLogger("MGR")


ENVS = {
    "host": os.getenv("POSTGRES_HOST"),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}
CONNINFO = " ".join([f"{name}={value}" for name, value in ENVS.items()])


def _get_conn() -> Connection:
    return Connection.connect(CONNINFO)


@retry(delay=0.5, backoff=2)
def get_conn():
    try:
        conn = _get_conn()
        conn.autocommit = True
        return conn
    except Exception as e:
        logger.error(f"{e}\nAquiring connection to db failed. Retrying...")
        raise


def get_unprocessed_subm(conn: Connection) -> Subm | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id, code, lang, round_id
            FROM submissions
            WHERE status = 'oczekiwanie'
            ORDER BY id ASC
            LIMIT 1
            """
        )
        res = cur.fetchone()

    if res is None:
        return None
    return Subm(**res)


def set_status(subm_id: int, status: Status, conn: Connection) -> None:
    conn.execute(
        """
        UPDATE submissions
        SET status = %s
        WHERE id = %s
        """,
        (status, subm_id),
    )


def set_message(subm_id: int, msg: str, conn: Connection) -> None:
    conn.execute(
        """
        UPDATE submissions
        SET status_msg = %s
        WHERE id = %s
        """,
        (msg, subm_id),
    )
