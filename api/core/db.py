import os
from typing import AsyncGenerator

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
