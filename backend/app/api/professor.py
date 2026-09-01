"""Professor-only read dashboard."""

from fastapi import APIRouter

from ...schemas.auth import ProfessorDashboardResponse
from ...services import professor
from ..auth_dependencies import ProfessorPrincipal

router = APIRouter(prefix="/api/professor", tags=["professor"])


@router.get("/dashboard", response_model=ProfessorDashboardResponse)
def dashboard(principal: ProfessorPrincipal) -> ProfessorDashboardResponse:
    del principal
    return professor.get_professor_dashboard()
