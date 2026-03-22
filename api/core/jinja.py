import os

from fastapi.templating import Jinja2Templates
from jinja2 import FileSystemBytecodeCache
from psycopg import AsyncConnection

from api.core.db import get_round

bytecode_cache = FileSystemBytecodeCache("/tmp/")

templates = Jinja2Templates(
    directory="templates", auto_reload=False, bytecode_cache=bytecode_cache
)
templates.env.globals.update({"website": os.getenv("WEBSITE_NAME")})


async def get_round_context(conn: AsyncConnection):
    return {"round": await get_round(conn)}
