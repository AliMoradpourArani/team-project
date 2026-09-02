"""Professor-only dashboards and review queue."""

from fastapi import APIRouter

from ...schemas.auth import ProfessorDashboardResponse
from ...schemas.github import ProfessorGitHubDashboardResponse
from ...schemas.project_review import ProfessorReviewQueueResponse
from ...services import github_integration, professor, project_reviews, queries
from ..auth_dependencies import ProfessorPrincipal

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
