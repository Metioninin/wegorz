from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from psycopg import AsyncConnection

from api.core.auth import get_user_info
from api.core.db import create_session, delete_session, get_conn, get_subms, is_password_valid
from api.core.jinja import templates
from api.core.models import ChangePassword, Login, Submission, User
from api.core.utils import gen_logout_redirect

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
    if user_info is not None:
        subms = await get_subms(conn, user_info.id)
    else:
        subms = None

    resp = gen_homepage_template(
        request, logged_in=user_info is not None, submissions=subms
    )
    if user_info is None:
        resp.delete_cookie("session")
    
    return resp


@router.post("/login")
async def post_login(
    request: Request, data: Login = Form(), conn: AsyncConnection = Depends(get_conn)
) -> Response:
    if not await is_password_valid(conn, data.login, data.password):
        return gen_homepage_template(
            request,
            logged_in=False,
            status_code=401,
            login_error="Niepoprawny login lub hasło.",
        )

    session = await create_session(conn, data.login)
    await conn.commit()

    if session is None:
        return gen_homepage_template(
            request,
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


def gen_change_pass_template(
    request: Request,
    status_code: int = 200,
    error: str | None = None,
    success: str | None = None,
) -> Response:
    context = {}

    if error:
        context["error"] = error
    if success:
        context["success"] = success

    return templates.TemplateResponse(
        request=request,
        name="change_pass.html",
        context=context,
        status_code=status_code,
    )


@router.get("/change-password")
async def get_change_password(
    request: Request, user_info: User | None = Depends(get_user_info)
) -> Response:
    if user_info is None:
        return gen_logout_redirect()
    return gen_change_pass_template(request)


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
        return gen_change_pass_template(
            request, status_code=401, error="Niepoprawne hasło."
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
        return gen_change_pass_template(
            request, error="Bład serwera. Spróbuj ponownie."
        )
    await conn.commit()

    response = gen_change_pass_template(request, success="Hasło zostało zmienione.")
    response.set_cookie("session", session, secure=True, httponly=True)
    return response
