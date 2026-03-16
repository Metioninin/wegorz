from typing import Literal, Self
from pydantic import AwareDatetime, BaseModel, Field, model_validator


class User(BaseModel):
    id: int
    login: str
    session: str


class Login(BaseModel):
    login: str
    password: str


class ChangePassword(BaseModel):
    current_password: str = Field(min_length=8, max_length=72)
    new_password: str = Field(min_length=8, max_length=72)
    confirm_password: str = Field(min_length=8, max_length=72)

    @model_validator(mode="after")
    def validate_passwords(self) -> Self:
        if self.current_password == self.new_password:
            raise ValueError("New password must be different from current one.")
        if self.new_password != self.confirm_password:
            raise ValueError("New and confirm passwords must be equal")
        return self


class Submission(BaseModel):
    id: int
    lang: str
    status: str
    send_at: AwareDatetime


class SubmissionDetail(Submission):
    code: str
    status_msg: str


class Submit(BaseModel):
    code: str
    lang: Literal["PY", "CPP"]