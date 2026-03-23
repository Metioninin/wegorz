import logging
import os
from typing import AsyncGenerator, Optional

from psycopg import AsyncConnection, sql
from psycopg.rows import dict_row

from api.core.models import Round, Submission, SubmissionDetail
from api.core.utils import gen_subm_detail_select, gen_subm_select

ENVS = {
    "host": os.getenv("POSTGRES_HOST"),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}
CONNINFO = " ".join([f"{name}={value}" for name, value in ENVS.items()])


ROUND_SELECT = sql.SQL(
    """
    (
        SELECT *
        FROM rounds
        WHERE now() <= ends_at
        ORDER BY ends_at
        LIMIT 1
    )
    UNION ALL
    (
        SELECT *
        FROM rounds
        ORDER BY ends_at DESC
        LIMIT 1
    )
    LIMIT 1
    """
)


async def get_conn() -> AsyncGenerator[AsyncConnection, None]:
    async with await AsyncConnection.connect(CONNINFO) as conn:
        yield conn
        await conn.rollback()


async def is_password_valid(conn: AsyncConnection, login: str, password: str) -> bool:
    async with conn.cursor() as cur:
        await cur.execute(
            """
            SELECT crypt(%s, password_hash) = password_hash
            FROM users
            WHERE login = %s
            """,
            (password, login),
        )
        res = await cur.fetchone()

    return res is not None and res[0] is True


async def create_session(conn: AsyncConnection, login: str) -> Optional[str]:
    async with conn.cursor() as cur:
        # lock user to ensure session won't be created after changing it
        await cur.execute(
            """
            SELECT id 
            FROM users 
            WHERE login = %s 
            FOR SHARE
            """,
            (login,),
        )
        res = await cur.fetchone()
        assert res is not None

        await cur.execute(
            """
            INSERT INTO sessions (id, user_id)
            VALUES (encode(gen_random_bytes(16), 'hex'), %s)
            RETURNING id
            """,
            (res[0],),
        )
        res = await cur.fetchone()

        if res is None:
            logging.info("Session insert failed, wow!")
            return None
        return res[0]


async def delete_session(conn: AsyncConnection, session: str) -> None:
    await conn.execute(
        """
        DELETE FROM sessions
        WHERE id = %s
        """,
        (session,),
    )


async def get_subms(conn: AsyncConnection, user_id: int) -> list[Submission]:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            sql.SQL(
                """
                SELECT {}, r.title AS round_title
                FROM submissions s
                JOIN rounds r ON r.id = s.round_id 
                WHERE s.user_id = %s
                ORDER BY id DESC
                """,
            ).format(gen_subm_select(prefix="s")),
            (user_id,),
        )
        res = await cur.fetchall()
    return [Submission(**row) for row in res]


async def get_subm(
    conn: AsyncConnection, subm_id: int, user_id: int
) -> SubmissionDetail | None:
    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            sql.SQL(
                """
                SELECT {}, r.title AS round_title
                FROM submissions s
                JOIN rounds r ON r.id = s.round_id
                WHERE s.id = %s AND s.user_id = %s
                """
            ).format(gen_subm_detail_select(prefix="s")),
            (subm_id, user_id),
        )
        res = await cur.fetchone()

    return SubmissionDetail(**res) if res else None


async def get_round(conn: AsyncConnection) -> Round:
    """
    Returns current or next round model
    """

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(ROUND_SELECT)
        res = await cur.fetchone()
        assert res is not None
    return Round(**res)


async def is_submit_time(conn: AsyncConnection) -> bool:
    async with conn.cursor() as cur:
        await cur.execute(
            sql.SQL(
                """
                SELECT now() BETWEEN starts_at AND ends_at
                FROM ({})
                """
            ).format(ROUND_SELECT),
        )
        res = await cur.fetchone()
        assert res is not None

    return res[0]


async def get_subms_cnt(conn: AsyncConnection, user_id: int) -> tuple[int, int]:
    async with conn.cursor() as cur:
        await cur.execute(
            sql.SQL(
                """
                WITH round AS ({})
                SELECT COUNT(*), (SELECT subms_limit FROM round)
                FROM submissions s
                WHERE s.user_id = %s AND s.round_id = (SELECT id FROM round)
                """
            ).format(ROUND_SELECT),
            (user_id,),
        )
        res = await cur.fetchone()
        assert res is not None

    return res[0], res[1]


async def has_submit_access(conn: AsyncConnection, user_id: int) -> bool:
    async with conn.cursor() as cur:
        await cur.execute(
            sql.SQL(
                """
                SELECT NOT r.restricted OR u.qualified 
                FROM ({}) r
                JOIN users u ON u.id = %(u)s
                """
            ).format(ROUND_SELECT),
            {"u": user_id},
        )
        res = await cur.fetchone()
        assert res is not None

    return res[0]


async def send_submit(conn: AsyncConnection, code: str, lang: str, user_id: int) -> int:
    async with conn.cursor() as cur:
        await cur.execute(
            sql.SQL(
                """
                WITH round AS ({})
                INSERT INTO submissions (code, lang, user_id, round_id)
                SELECT %s, %s, %s, id
                FROM round
                RETURNING id
                """
            ).format(ROUND_SELECT),
            (code, lang, user_id),
        )
        res = await cur.fetchone()
        assert res is not None
    return res[0]
