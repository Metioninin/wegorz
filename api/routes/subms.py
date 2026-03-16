from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request, Response
from fastapi.responses import RedirectResponse
from psycopg import AsyncConnection

from api.core.auth import get_user_info
from api.core.db import has_subms_left, is_submit_time, get_conn, get_subm, send_submit
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
        raise HTTPException(404)

    subm = await get_subm(conn, subm_id, user_info.id)

    if subm is None:
        raise HTTPException(404)

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

    if not await is_submit_time(conn, user_info.id):
        return templates.TemplateResponse(
            request=request,
            name="send.html",
            context={"error": "Czas na wysyłanie zgłoszeń się nie zaczął lub minął."},
        )

    # prevent two submits from being in the same time
    await conn.execute("SELECT pg_advisory_xact_lock(%s)", (user_info.id,))

    if not await has_subms_left(conn, user_info.id):
        return templates.TemplateResponse(
            request=request,
            name="send.html",
            context={"error": "Osiągnięto maksymalny limit zgłoszeń"},
        )

    code_size = len(data.code.encode("utf-8"))
    if code_size == 0 or code_size >= 100 * 1024:
        return templates.TemplateResponse(
            request=request,
            name="send.html",
            context={
                "error": "Rozmiar kodu musi być większy niż 0 i mniejszy niż 100KB."
            },
        )

    if "\x00" in data.code:
        return templates.TemplateResponse(
            request=request,
            name="send.html",
            context={"error": "Kod nie może zawierać bajtów zerowych (null bytes)."},
        )

    subm_id = await send_submit(conn, data.code, data.lang, user_info.id)
    await conn.commit()

    return RedirectResponse(f"/submission/{subm_id}", status_code=303)
