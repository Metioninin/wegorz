from datetime import datetime
from typing import Literal
from pydantic import AwareDatetime, BaseModel, Field


class User(BaseModel):
    id: int
    login: str
    session: str


class Login(BaseModel):
    login: str
    password: str


class ChangePassword(BaseModel):
    current_password: str = Field(max_length=72)
    new_password: str = Field(min_length=8, max_length=72)
    confirm_password: str = Field(min_length=8, max_length=72)


class Submission(BaseModel):
    id: int
    lang: str
    status: str
    round_title: str
    send_at: AwareDatetime


class SubmissionDetail(Submission):
    code: str
    status_msg: str


class Submit(BaseModel):
    code: str
    lang: Literal["PY", "CPP"]


class Round(BaseModel):
    title: str
    description: str
    
    subms_limit: int
    statement_name: str

    starts_at: datetime
    ends_at: datetime