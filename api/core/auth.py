from fastapi import Cookie, Depends
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from api.core.db import get_conn
from api.core.models import User


async def get_user_info(
    conn: AsyncConnection = Depends(get_conn),
    session: str | None = Cookie(default=None),
) -> User | None:
    if session is None:
        return None

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT id AS session, login
            FROM sessions
            WHERE id = %s
            """,
            (session,),
        )
        res = await cur.fetchone()

        if res is None:
            return None

    return User(**res)
