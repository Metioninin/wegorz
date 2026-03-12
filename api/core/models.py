from pydantic import BaseModel


class User(BaseModel):
    id: int


class Login(BaseModel):
    login: str
    password: str
