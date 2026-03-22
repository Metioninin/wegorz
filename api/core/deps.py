from fastapi import Cookie, Depends
from psycopg import AsyncConnection
from psycopg.rows import dict_row

from api.core.db import get_conn, get_round as db_get_round
from api.core.models import Round, User


async def get_user_info(
    conn: AsyncConnection = Depends(get_conn),
    session: str | None = Cookie(default=None),
) -> User | None:
    if session is None:
        return None

    async with conn.cursor(row_factory=dict_row) as cur:
        await cur.execute(
            """
            SELECT 
                u.id AS id, 
                s.id AS session,
                u.login AS login
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.id = %s
            """,
            (session,),
        )
        res = await cur.fetchone()

        if res is None:
            return None

    return User(**res)


async def get_round(conn: AsyncConnection = Depends(get_conn)) -> Round:
    return await db_get_round(conn)
