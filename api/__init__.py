from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.routes import home, subms

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

app.mount("/static/css", StaticFiles(directory="static/css"), name="static/css")
app.mount("/static/favicon", StaticFiles(directory="static/favicon"), name="static/favicon")


for module in (home, subms):
    app.include_router(module.router)
