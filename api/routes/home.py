from fastapi import APIRouter, Depends, Request

from api.core.auth import get_user_info
from api.core.jinja import templates
from api.core.models import User

router = APIRouter()


def gen_homepage_template(
    request: Request,
    logged_in: bool,
    status_code: int = 200,
    login_error: str | None = None,
):
    return templates.TemplateResponse(
        request=request,
        status_code=status_code,
        name="home.html",
        context={"logged_in": logged_in, "login_error": login_error},
    )


@router.get("/")
async def homepage(request: Request, user_info: User | None = Depends(get_user_info)):
    return gen_homepage_template(request, logged_in=user_info is not None)
