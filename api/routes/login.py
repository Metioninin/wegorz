import logging

from fastapi import Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRouter
from psycopg import AsyncConnection

from api.core.auth import get_user_info
from api.core.db import get_conn
from api.core.jinja import templates
from api.core.models import Login, User

router = APIRouter()


def gen_login_template(
    request: Request, status_code: int = 200, error: str | None = None
) -> Response:
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": error} if error else {},
        status_code=status_code,
    )


@router.get("/login")
async def get_login(
    request: Request, user_info: User | None = Depends(get_user_info)
) -> Response:
    if user_info is not None:
        return RedirectResponse(url="/", status_code=303)
    return gen_login_template(request)


@router.post("/login")
async def post_login(
    request: Request, data: Login = Form(), conn: AsyncConnection = Depends(get_conn)
) -> Response:
    async with conn.cursor() as cur:
        # verify credentials
        await cur.execute(
            """
            SELECT crypt(%s, password_hash) = password_hash, id
            FROM users
            WHERE login = %s
            """,
            (data.password, data.login),
        )
        res = await cur.fetchone()

        if res is None or res[0] is False:
            return gen_login_template(
                request, status_code=401, error="Incorrect login or password."
            )

        # insert new session
        await cur.execute(
            """
            INSERT INTO sessions (id, user_id)
            VALUES (encode(gen_random_bytes(16), 'hex'), %s)
            RETURNING id
            """,
            (res[1],),
        )
        res = await cur.fetchone()

        if res is None:
            logging.info("Somebody was pretty lucky with creating new session")
            return gen_login_template(
                request, status_code=500, error="Internal sever error. Try again."
            )

        session = res[0]

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("session", session)

    return response
