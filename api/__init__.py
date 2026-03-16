from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from api.routes import home, login, subms

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


for module in (home, login, subms):
    app.include_router(module.router)
