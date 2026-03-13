import logging
import os
from typing import AsyncGenerator, Optional

from psycopg import AsyncConnection

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
        # insert new session
        await cur.execute(
            """
            INSERT INTO sessions (id, login)
            VALUES (encode(gen_random_bytes(16), 'hex'), %s)
            RETURNING id
            """,
            (login,),
        )
        res = await cur.fetchone()

        if res is None:
            logging.info("Session insert failed, wow!")
            return None
        return res[0]