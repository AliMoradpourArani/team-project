"""Student GitHub sync and import routes."""

from fastapi import APIRouter, HTTPException, status

from ...schemas.github_editor import (
    GithubConnectInput,
    GithubImportInput,
    GithubImportResponse,
    GithubRepo,
    GithubStatus,
)
from ...services import github_sync
from ..auth_dependencies import CsrfPrincipal, StudentPrincipal

router = APIRouter(prefix="/api/github", tags=["github"])


def _require_student(principal) -> None:
    if principal.role != "student" or principal.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can manage their GitHub integration.",
        )


@router.get("/status", response_model=GithubStatus)
def github_status(principal: StudentPrincipal) -> GithubStatus:
    return github_sync.get_status(principal.user_id)


@router.post("/connect", response_model=GithubStatus)
def github_connect(
    payload: GithubConnectInput, principal: CsrfPrincipal
) -> GithubStatus:
    _require_student(principal)
    return github_sync.connect_github(principal.user_id, payload.username, payload.token)


@router.post("/disconnect", response_model=GithubStatus)
def github_disconnect(principal: CsrfPrincipal) -> GithubStatus:
    _require_student(principal)
    return github_sync.disconnect_github(principal.user_id)


@router.get("/repos", response_model=list[GithubRepo])
def github_repos(principal: StudentPrincipal) -> list[GithubRepo]:
    return github_sync.list_repos(principal.user_id)


@router.post("/import", response_model=GithubImportResponse)
def github_import(
    payload: GithubImportInput, principal: CsrfPrincipal
) -> GithubImportResponse:
    _require_student(principal)
    return github_sync.import_repository(principal.user_id, payload.fullName)
