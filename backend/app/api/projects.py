"""Project routes with role-based visibility."""

from fastapi import APIRouter

from ...schemas.api import ProjectResponse
from ...services import queries
from ..auth_dependencies import CurrentPrincipal

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects(principal: CurrentPrincipal) -> list[ProjectResponse]:
    projects = queries.list_projects()
    if principal.role == "professor":
        return projects
    return [project for project in projects if project.userId == principal.user_id]
