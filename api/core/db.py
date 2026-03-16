import logging
import os
from typing import AsyncGenerator, Optional

from psycopg import AsyncConnection, sql
from psycopg.rows import dict_row

from api.core.models import Submission, SubmissionDetail

ENVS = {
    "host": os.getenv("POSTGRES_HOST"),
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
}
CONNINFO = " ".join([f"{name}={value}" for name, value in ENVS.items()])


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
            (login,)
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
        (session,)
    )


async def get_subms(conn: AsyncConnection, user_id: int) -> list[Submission]:
    columns = [sql.Identifier(column) for column in Submission.model_fields]

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            sql.SQL(
                """
                SELECT {}
                FROM submissions
                WHERE user_id = %s
                """,
            ).format(sql.SQL(", ").join(columns)),
            (user_id,),
        )
        res = await cur.fetchall()
    return [Submission(**row) for row in res]


async def get_subm(conn: AsyncConnection, subm_id: int, user_id: int) -> SubmissionDetail | None:
    columns = [sql.Identifier(column) for column in SubmissionDetail.model_fields]

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            sql.SQL(
                """
                SELECT {}
                FROM submissions
                WHERE id = %s AND user_id = %s
                """
            ).format(sql.SQL(", ").join(columns)),
            (subm_id, user_id),
        )
        res = await cur.fetchone()

    return SubmissionDetail(**res) if res else None


async def send_submit(conn: AsyncConnection, code: str, lang: str, user_id: int) -> int:
    async with conn.cursor() as cur:
        await cur.execute(
            """
            INSERT INTO submissions (code, lang, user_id)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (code, lang, user_id),
        )
        res = await cur.fetchone()
        assert res is not None
    return res[0]


async def can_submit(conn: AsyncConnection, user_id: int) -> bool:
    async with conn.cursor() as cur:
        await cur.execute(
            """
            SELECT now() BETWEEN starts_at AND ends_at
            FROM contest c
            JOIN users u ON u.id = %s
            LIMIT 1
            """,
            (user_id,)
        )
        res = await cur.fetchone()
        assert res is not None

    return res[0]