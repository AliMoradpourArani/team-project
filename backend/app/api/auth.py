"""Login, logout, and current-session routes."""

from fastapi import APIRouter, HTTPException, Request, Response, status

from ...schemas.auth import AuthMeResponse, LoginRequest
from ...services import auth
from ..auth_dependencies import CsrfPrincipal, CurrentPrincipal

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _me(principal: auth.Principal) -> AuthMeResponse:
    return AuthMeResponse(
        username=principal.username,
        displayName=auth.display_name(principal),
        role=principal.role,
        userId=principal.user_id,
        csrfToken=principal.csrf_token,
    )


@router.post("/login", response_model=AuthMeResponse)
def login(payload: LoginRequest, response: Response) -> AuthMeResponse:
    try:
        principal, token = auth.authenticate(payload.username, payload.password)
    except (PermissionError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        ) from exc

    response.set_cookie(
        key=auth.session_cookie_name(),
        value=token,
        max_age=auth.session_hours() * 3600,
        httponly=True,
        secure=auth.cookie_secure(),
        samesite="lax",
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return _me(principal)


@router.get("/me", response_model=AuthMeResponse)
def me(principal: CurrentPrincipal) -> AuthMeResponse:
    return _me(principal)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    principal: CsrfPrincipal,
) -> Response:
    del principal
    token = request.cookies.get(auth.session_cookie_name(), "")
    auth.delete_session(token)
    response.delete_cookie(
        key=auth.session_cookie_name(),
        path="/",
        secure=auth.cookie_secure(),
        httponly=True,
        samesite="lax",
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response
