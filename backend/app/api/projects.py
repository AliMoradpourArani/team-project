"""Project routes with role-based visibility and controlled local execution."""

from fastapi import APIRouter, HTTPException, status

from ...schemas.api import ProjectResponse
from ...schemas.project_runner import ProjectIntegrationResponse, ProjectRunResponse
from ...services import project_runner, queries
from ..auth_dependencies import CsrfPrincipal, CurrentPrincipal

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _visible_projects(principal: CurrentPrincipal) -> list[ProjectResponse]:
    projects = queries.list_projects()
    if principal.role == "professor":
        return projects
    return [project for project in projects if project.userId == principal.user_id]


def _project_for_principal(project_id: str, principal: CurrentPrincipal) -> ProjectResponse:
    projects = _visible_projects(principal)
    project = next((candidate for candidate in projects if candidate.id == project_id), None)
    if project is None:
        raise queries.NotFoundError(f"Unknown or inaccessible project: {project_id}")
    return project


@router.get("", response_model=list[ProjectResponse])
def list_projects(principal: CurrentPrincipal) -> list[ProjectResponse]:
    return _visible_projects(principal)


@router.get("/integrations", response_model=list[ProjectIntegrationResponse])
def list_project_integrations(principal: CurrentPrincipal) -> list[ProjectIntegrationResponse]:
    return project_runner.list_integrations(_visible_projects(principal))


@router.post("/{project_id}/run", response_model=ProjectRunResponse)
def run_project(project_id: str, principal: CsrfPrincipal) -> ProjectRunResponse:
    project = _project_for_principal(project_id, principal)
    try:
        return project_runner.run_project(project)
    except project_runner.ProjectRunnerDisabled as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except project_runner.ProjectManifestError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except project_runner.ProjectRunnerError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error
