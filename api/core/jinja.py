from fastapi.templating import Jinja2Templates
from jinja2 import FileSystemBytecodeCache
from psycopg import AsyncConnection

from api.core.db import get_settings

bytecode_cache = FileSystemBytecodeCache("/tmp/")

templates = Jinja2Templates(
    directory="templates", auto_reload=False, bytecode_cache=bytecode_cache
)
templates.env.globals.update({"website": "Węgorz"})


async def get_contest_settings(conn: AsyncConnection):
    return {"contest_settings": await get_settings(conn)}
