"""Professor-only dashboards, review queue, submissions, and releases."""

from fastapi import APIRouter, HTTPException, status

from ...schemas.auth import ProfessorDashboardResponse
from ...schemas.github import ProfessorGitHubDashboardResponse
from ...schemas.project_review import ProfessorReviewQueueResponse
from ...schemas.submission import (
    ProfessorSubmissionDashboardResponse,
    SubmissionReleaseDetail,
    SubmissionReleaseInput,
    SubmissionReleaseSummary,
    SubmissionSettingsInput,
    SubmissionSettingsResponse,
)
from ...services import github_integration, professor, project_reviews, queries, submissions
from ..auth_dependencies import ProfessorCsrfPrincipal, ProfessorPrincipal

router = APIRouter(prefix="/api/professor", tags=["professor"])


@router.get("/dashboard", response_model=ProfessorDashboardResponse)
def dashboard(principal: ProfessorPrincipal) -> ProfessorDashboardResponse:
    del principal
    return professor.get_professor_dashboard()


@router.get("/github", response_model=ProfessorGitHubDashboardResponse)
def github_dashboard(principal: ProfessorPrincipal) -> ProfessorGitHubDashboardResponse:
    del principal
    return github_integration.get_professor_github_dashboard()


@router.get("/reviews", response_model=ProfessorReviewQueueResponse)
def review_queue(principal: ProfessorPrincipal) -> ProfessorReviewQueueResponse:
    del principal
    return project_reviews.get_review_queue(queries.list_projects())


@router.get("/submissions", response_model=ProfessorSubmissionDashboardResponse)
def submission_dashboard(principal: ProfessorPrincipal) -> ProfessorSubmissionDashboardResponse:
    del principal
    return submissions.get_professor_dashboard(queries.list_projects())


@router.put("/submission-settings", response_model=SubmissionSettingsResponse)
def update_submission_settings(
    payload: SubmissionSettingsInput,
    principal: ProfessorCsrfPrincipal,
) -> SubmissionSettingsResponse:
    return submissions.save_settings(principal.account_id, payload)


@router.get("/releases", response_model=list[SubmissionReleaseSummary])
def releases(principal: ProfessorPrincipal) -> list[SubmissionReleaseSummary]:
    del principal
    return submissions.list_releases()


@router.get("/releases/{release_id}", response_model=SubmissionReleaseDetail)
def release_detail(release_id: int, principal: ProfessorPrincipal) -> SubmissionReleaseDetail:
    del principal
    try:
        return submissions.get_release(release_id)
    except submissions.SubmissionConflict as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.post("/releases", response_model=SubmissionReleaseDetail)
def create_release(
    payload: SubmissionReleaseInput,
    principal: ProfessorCsrfPrincipal,
) -> SubmissionReleaseDetail:
    try:
        return submissions.create_release(queries.list_projects(), principal.account_id, payload)
    except submissions.SubmissionConflict as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
