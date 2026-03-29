from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from api.routes import home, subms

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

app.mount("/static/css", StaticFiles(directory="static/css"), name="static/css")

@app.get("/favicon.ico")
async def favicon():
    return FileResponse("static/favicon/favicon.ico")

for module in (home, subms):
    app.include_router(module.router)
