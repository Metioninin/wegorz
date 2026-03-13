from fastapi import FastAPI
from api.routes import home, login, subms

app = FastAPI()


for module in (home, login, subms):
    app.include_router(module.router)
