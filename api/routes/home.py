from fastapi import APIRouter, Depends, Request, Response
from psycopg import AsyncConnection

from api.core.auth import get_user_info
from api.core.db import get_conn, get_subms
from api.core.jinja import templates
from api.core.models import Submission, User

router = APIRouter()


def gen_homepage_template(
    request: Request,
    logged_in: bool,
    status_code: int = 200,
    login_error: str | None = None,
    submissions: list[Submission] | None = None,
):
    if submissions is None:
        submissions = []

    return templates.TemplateResponse(
        request=request,
        status_code=status_code,
        name="home.html",
        context={
            "logged_in": logged_in,
            "login_error": login_error,
            "submissions": submissions,
        },
    )


@router.get("/")
async def homepage(
    request: Request,
    user_info: User | None = Depends(get_user_info),
    conn: AsyncConnection = Depends(get_conn),
) -> Response:
    subms = None

    if user_info is not None:
        subms = await get_subms(conn, user_info.login)

    return gen_homepage_template(
        request, logged_in=user_info is not None, submissions=subms
    )
