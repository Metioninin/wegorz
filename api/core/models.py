from typing import Self
from pydantic import BaseModel, Field, ValidationError, model_validator


def get_first_error(exc: ValidationError):
    msg = exc.errors()[0]["msg"]
    msg = msg.removeprefix("Value error, ")
    return msg


class User(BaseModel):
    login: str


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
