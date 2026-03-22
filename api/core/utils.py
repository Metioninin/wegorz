from typing import Type
from fastapi.responses import RedirectResponse
from psycopg import sql
from pydantic import BaseModel

from api.core.models import Submission, SubmissionDetail


def gen_logout_redirect() -> RedirectResponse:
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session")
    return response


def _gen_subm_select(model: Type[BaseModel], prefix: str) -> sql.Composable:
    if prefix:
        schema = "{}.{}"
    else:
        schema = "{}{}"

    columns = [
        sql.SQL(schema).format(sql.Identifier(prefix), sql.Identifier(column))
        for column in model.model_fields.keys() - {"round_title"}
    ]
    return sql.SQL(", ").join(columns)


def gen_subm_select(prefix: str = "") -> sql.Composable:
    return _gen_subm_select(Submission, prefix)


def gen_subm_detail_select(prefix: str = "") -> sql.Composable:
    return _gen_subm_select(SubmissionDetail, prefix)
