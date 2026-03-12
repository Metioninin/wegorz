from fastapi import APIRouter, Request

from api.core.jinja import templates

router = APIRouter()


@router.get("/")
async def homepage(request: Request):
    return templates.TemplateResponse(request=request, name="home.html")
