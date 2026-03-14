from fastapi.responses import RedirectResponse


def gen_logout_redirect() -> RedirectResponse:
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("session")
    return response
