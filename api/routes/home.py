from datetime import datetime, UTC
from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from psycopg import AsyncConnection

from api.core.auth import get_user_info
from api.core.db import (
    create_session,
    delete_session,
    get_conn,
    get_settings,
    get_subms,
    is_password_valid,
)
from api.core.jinja import get_contest_settings, templates
from api.core.models import ChangePassword, Login, Submission, User
from api.core.utils import gen_logout_redirect

router = APIRouter()


async def gen_homepage_template(
    request: Request,
    conn: AsyncConnection,
    logged_in: bool,
    status_code: int = 200,
    login_error: str | None = None,
    submissions: list[Submission] | None = None,
):
    if submissions is None:
        submissions = []

    context = {
        "logged_in": logged_in,
        "login_error": login_error,
        "submissions": submissions,
        "now": datetime.now(UTC),
    }
    if logged_in:
        context |= await get_contest_settings(conn)

    return templates.TemplateResponse(
        request=request, status_code=status_code, name="home.html", context=context
    )


async def gen_change_pass_template(
    request: Request,
    conn: AsyncConnection,
    status_code: int = 200,
    error: str | None = None,
    success: str | None = None,
) -> Response:
    context = {}

    if error:
        context["error"] = error
    if success:
        context["success"] = success

    context |= await get_contest_settings(conn)

    return templates.TemplateResponse(
        request=request,
        name="change_pass.html",
        context=context,
        status_code=status_code,
    )


@router.get("/")
async def homepage(
    request: Request,
    user_info: User | None = Depends(get_user_info),
    conn: AsyncConnection = Depends(get_conn),
) -> Response:
    if user_info is not None:
        subms = await get_subms(conn, user_info.id)
    else:
        subms = None

    resp = await gen_homepage_template(
        request, conn, logged_in=user_info is not None, submissions=subms
    )
    if user_info is None:
        resp.delete_cookie("session")

    return resp


@router.post("/login")
async def post_login(
    request: Request, data: Login = Form(), conn: AsyncConnection = Depends(get_conn)
) -> Response:
    if not await is_password_valid(conn, data.login, data.password):
        return await gen_homepage_template(
            request,
            conn,
            logged_in=False,
            status_code=401,
            login_error="Niepoprawny login lub hasło.",
        )

    session = await create_session(conn, data.login)
    await conn.commit()

    if session is None:
        return await gen_homepage_template(
            request,
            conn,
            logged_in=False,
            status_code=500,
            login_error="Bład serwera. Spróbuj ponownie.",
        )

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie("session", session, secure=True, httponly=True)

    return response


@router.post("/logout")
async def post_logout(
    user_info: User | None = Depends(get_user_info),
    conn: AsyncConnection = Depends(get_conn),
) -> Response:
    if user_info is not None:
        await delete_session(conn, user_info.session)
    return gen_logout_redirect()


@router.get("/change-password")
async def get_change_password(
    request: Request,
    user_info: User | None = Depends(get_user_info),
    conn: AsyncConnection = Depends(get_conn),
) -> Response:
    if user_info is None:
        return gen_logout_redirect()
    return await gen_change_pass_template(request, conn)


@router.post("/change-password")
async def post_change_password(
    request: Request,
    data: ChangePassword = Form(),
    user_info: User | None = Depends(get_user_info),
    conn: AsyncConnection = Depends(get_conn),
) -> Response:
    if user_info is None:
        return gen_logout_redirect()

    if not await is_password_valid(conn, user_info.login, data.current_password):
        return await gen_change_pass_template(
            request, conn, status_code=401, error="Niepoprawne hasło."
        )

    await conn.execute(
        """
        UPDATE users
        SET password_hash = crypt(%s, gen_salt('bf'))
        WHERE id = %s
        """,
        (data.new_password, user_info.id),
    )

    # clear previous sessions and create new
    await conn.execute(
        """
        DELETE FROM sessions
        WHERE user_id = %s
        """,
        (user_info.id,),
    )
    session = await create_session(conn, user_info.login)

    if session is None:
        await conn.rollback()
        return await gen_change_pass_template(
            request, conn, error="Bład serwera. Spróbuj ponownie."
        )
    await conn.commit()

    response = await gen_change_pass_template(
        request, conn, success="Hasło zostało zmienione."
    )
    response.set_cookie("session", session, secure=True, httponly=True)
    return response


@router.get("/statement")
async def statement(
    user_info: User | None = Depends(get_user_info),
    conn: AsyncConnection = Depends(get_conn)
) -> Response:
    if user_info is None:
        return RedirectResponse("/", status_code=303)

    settings = await get_settings(conn)
        
    if datetime.now().astimezone() < settings.starts_at:
        raise HTTPException(403)

    return FileResponse("static/tresc.pdf")
