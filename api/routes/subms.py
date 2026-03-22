from fastapi import APIRouter, Depends, Form, HTTPException, Path, Request, Response
from fastapi.responses import RedirectResponse
from psycopg import AsyncConnection

from api.core.deps import get_user_info
from api.core.db import (
    has_submit_access,
    has_subms_left,
    is_submit_time,
    get_conn,
    get_subm,
    send_submit,
)
from api.core.models import SubmissionDetail, Submit, User
from api.core.jinja import get_round_context, templates
from api.core.utils import gen_logout_redirect

router = APIRouter()


async def gen_submission_template(
    request: Request, conn: AsyncConnection, submission: SubmissionDetail
) -> Response:
    context = {"submission": submission}
    context |= await get_round_context(conn)

    return templates.TemplateResponse(
        request=request, name="subm.html", context=context
    )


async def gen_submit_template(
    request: Request, conn: AsyncConnection, error: str | None = None
) -> Response:
    context = {"error": error} if error else {}
    context |= await get_round_context(conn)

    return templates.TemplateResponse(
        request=request, name="send.html", context=context
    )


@router.get("/submission/{subm_id}")
async def get_submission_details(
    request: Request,
    subm_id: int = Path(),
    user_info: User | None = Depends(get_user_info),
    conn: AsyncConnection = Depends(get_conn),
) -> Response:
    if user_info is None:
        raise HTTPException(404)

    submission = await get_subm(conn, subm_id, user_info.id)

    if submission is None:
        raise HTTPException(404)

    return await gen_submission_template(request, conn, submission)


@router.get("/submit")
async def get_submit(
    request: Request,
    user_info: User | None = Depends(get_user_info),
    conn: AsyncConnection = Depends(get_conn),
) -> Response:
    if user_info is None:
        return gen_logout_redirect()
    return await gen_submit_template(request, conn)


@router.post("/submit")
async def post_submit(
    request: Request,
    data: Submit = Form(),
    user_info: User | None = Depends(get_user_info),
    conn: AsyncConnection = Depends(get_conn),
) -> Response:
    if user_info is None:
        return gen_logout_redirect()

    if not await is_submit_time(conn):
        return await gen_submit_template(
            request, conn, error="Czas na wysyłanie zgłoszeń się nie zaczął lub minął."
        )

    if not await has_submit_access(conn, user_info.id):
        return await gen_submit_template(
            request,
            conn,
            error="Nie możesz wysłać zgłoszenia, bo nie zakwalifikowałeś się do tej rundy.",
        )

    # prevent two submits from being in the same time
    await conn.execute("SELECT pg_advisory_xact_lock(%s)", (user_info.id,))

    if not await has_subms_left(conn, user_info.id):
        return await gen_submit_template(
            request, conn, error="Osiągnięto maksymalny limit zgłoszeń"
        )

    code_size = len(data.code.encode("utf-8"))
    if code_size == 0 or code_size >= 100 * 1024:
        return await gen_submit_template(
            request,
            conn,
            error="Rozmiar kodu musi być większy niż 0 i mniejszy niż 100KB.",
        )

    if "\x00" in data.code:
        return await gen_submit_template(
            request, conn, error="Kod nie może zawierać bajtów zerowych (null bytes)."
        )

    subm_id = await send_submit(conn, data.code, data.lang, user_info.id)
    await conn.commit()

    return RedirectResponse(f"/submission/{subm_id}", status_code=303)
