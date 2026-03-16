from fastapi.templating import Jinja2Templates
from jinja2 import FileSystemBytecodeCache

bytecode_cache = FileSystemBytecodeCache("/tmp/")
templates = Jinja2Templates(
    directory="templates", auto_reload=False, bytecode_cache=bytecode_cache
)

templates.env.globals.update({"website": "Węgorz"})
