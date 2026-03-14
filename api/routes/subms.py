from fastapi import APIRouter, Depends, Form, Path, Request, Response
from fastapi.responses import RedirectResponse
from psycopg import AsyncConnection

from api.core.auth import get_user_info
from api.core.db import can_submit, get_conn, get_subm, send_submit
from api.core.models import Submit, User
from api.core.jinja import templates
from api.core.utils import gen_logout_redirect

router = APIRouter()


@router.get("/submission/{subm_id}")
async def get_submission_details(
    request: Request,
    subm_id: int = Path(),
    user_info: User | None = Depends(get_user_info),
    conn: AsyncConnection = Depends(get_conn),
) -> Response:
    if user_info is None:
        return gen_logout_redirect()

    subm = await get_subm(conn, subm_id, user_info.login)

    if subm is None:
        return templates.TemplateResponse(
            request=request, name="404.html", status_code=404
        )

    return templates.TemplateResponse(
        request=request, name="subm.html", context={"submission": subm}
    )


@router.get("/submit")
async def get_submit(
    request: Request, user_info: User | None = Depends(get_user_info)
) -> Response:
    if user_info is None:
        return gen_logout_redirect()
    return templates.TemplateResponse(request=request, name="send.html")


@router.post("/submit")
async def post_submit(
    request: Request,
    data: Submit = Form(),
    user_info: User | None = Depends(get_user_info),
    conn: AsyncConnection = Depends(get_conn),
) -> Response:
    if user_info is None:
        return gen_logout_redirect()

    if not await can_submit(conn, user_info.login):
        return templates.TemplateResponse(
            request=request,
            name="send.html",
            context={"error": "Czas na wysyłanie zgłoszeń się nie zaczął lub minął."},
        )

    subm_id = await send_submit(conn, data.code, data.lang, user_info.login)
    await conn.commit()

    return RedirectResponse(f"/submission/{subm_id}", status_code=303)
