from fastapi import FastAPI
from api.routes import home, login

app = FastAPI()


for module in (home, login):
    app.include_router(module.router)
