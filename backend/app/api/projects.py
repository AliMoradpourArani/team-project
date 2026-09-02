"""Project routes with role-based visibility, reviews, submissions, and controlled execution."""

from fastapi import APIRouter, HTTPException, Response, status

from ...schemas.api import ProjectResponse
from ...schemas.project_review import ProjectReviewInput, ProjectReviewResponse
from ...schemas.project_runner import (
    ProjectDetailResponse,
    ProjectIntegrationResponse,
    ProjectRunResponse,
)
from ...schemas.submission import ProjectSubmissionResponse, ProjectSubmissionStatusResponse
from ...services import project_reviews, project_runner, queries, submissions
from ..auth_dependencies import CsrfPrincipal, CurrentPrincipal, ProfessorCsrfPrincipal

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


@router.get("/{project_id}/detail", response_model=ProjectDetailResponse)
def get_project_detail(project_id: str, principal: CurrentPrincipal) -> ProjectDetailResponse:
    project = _project_for_principal(project_id, principal)
    try:
        return project_runner.project_detail(project)
    except project_runner.ProjectRunnerError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error


@router.get("/{project_id}/review", response_model=ProjectReviewResponse | None)
def get_project_review(
    project_id: str, principal: CurrentPrincipal
) -> ProjectReviewResponse | None:
    _project_for_principal(project_id, principal)
    return project_reviews.get_review(project_id)


@router.put("/{project_id}/review", response_model=ProjectReviewResponse)
def save_project_review(
    project_id: str,
    payload: ProjectReviewInput,
    principal: ProfessorCsrfPrincipal,
) -> ProjectReviewResponse:
    _project_for_principal(project_id, principal)
    return project_reviews.save_review(project_id, principal.account_id, payload)


@router.delete("/{project_id}/review", status_code=status.HTTP_204_NO_CONTENT)
def delete_project_review(project_id: str, principal: ProfessorCsrfPrincipal) -> Response:
    _project_for_principal(project_id, principal)
    project_reviews.delete_review(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{project_id}/submission", response_model=ProjectSubmissionStatusResponse)
def get_project_submission(
    project_id: str, principal: CurrentPrincipal
) -> ProjectSubmissionStatusResponse:
    _project_for_principal(project_id, principal)
    return submissions.get_project_status(project_id)


@router.post("/{project_id}/submit", response_model=ProjectSubmissionResponse)
def submit_project(project_id: str, principal: CsrfPrincipal) -> ProjectSubmissionResponse:
    if principal.role != "student" or principal.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can create project submissions.",
        )
    project = _project_for_principal(project_id, principal)
    try:
        return submissions.submit_project(project, principal.account_id)
    except submissions.SubmissionConflict as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.post("/{project_id}/run", response_model=ProjectRunResponse)
def run_project(project_id: str, principal: CsrfPrincipal) -> ProjectRunResponse:
    project = _project_for_principal(project_id, principal)
    try:
        result = project_runner.run_project(project)
        project_runner.record_run(result)
        return result
    except project_runner.ProjectRunnerDisabled as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error)) from error
    except project_runner.ProjectManifestError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    except project_runner.ProjectRunnerError as error:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(error)) from error
