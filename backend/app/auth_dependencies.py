"""FastAPI authentication, role, and CSRF dependencies."""

from __future__ import annotations

import hmac
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from ..services import auth


def get_current_principal(request: Request) -> auth.Principal:
    token = request.cookies.get(auth.session_cookie_name(), "")
    principal = auth.resolve_session(token)
    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return principal


CurrentPrincipal = Annotated[auth.Principal, Depends(get_current_principal)]


def require_professor(principal: CurrentPrincipal) -> auth.Principal:
    if principal.role != "professor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Professor access required.",
        )
    return principal


ProfessorPrincipal = Annotated[auth.Principal, Depends(require_professor)]


def require_student(principal: CurrentPrincipal) -> auth.Principal:
    if principal.role != "student" or principal.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student access required.",
        )
    return principal


StudentPrincipal = Annotated[auth.Principal, Depends(require_student)]


def _verify_csrf(request: Request, principal: auth.Principal) -> auth.Principal:
    supplied = request.headers.get("X-CSRF-Token", "")
    if not supplied or not hmac.compare_digest(supplied, principal.csrf_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid CSRF token.",
        )
    return principal


def require_csrf(request: Request, principal: CurrentPrincipal) -> auth.Principal:
    return _verify_csrf(request, principal)


CsrfPrincipal = Annotated[auth.Principal, Depends(require_csrf)]


def require_professor_csrf(request: Request, principal: ProfessorPrincipal) -> auth.Principal:
    return _verify_csrf(request, principal)


ProfessorCsrfPrincipal = Annotated[auth.Principal, Depends(require_professor_csrf)]
