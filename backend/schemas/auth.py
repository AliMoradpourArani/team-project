"""Authentication and professor-dashboard API contracts."""

from pydantic import BaseModel, ConfigDict, Field

from .api import ActivityResponse, UserResponse


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=8, max_length=200)


class AuthMeResponse(BaseModel):
    username: str
    displayName: str
    role: str
    userId: str | None = None
    csrfToken: str


class ProfessorMemberSummary(BaseModel):
    user: UserResponse
    totalActivities: int
    completedActivities: int
    inProgressActivities: int
    plannedActivities: int
    activeProjects: int
    latestActivityDate: str | None = None


class ProfessorTotals(BaseModel):
    members: int
    activities: int
    completedActivities: int
    activeProjects: int


class ProfessorDashboardResponse(BaseModel):
    totals: ProfessorTotals
    members: list[ProfessorMemberSummary]
    recentActivities: list[ActivityResponse]
