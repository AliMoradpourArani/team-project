"""Professor project-review and rubric API contracts."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from .api import ProjectResponse

ReviewStatus = Literal["in-review", "changes-requested", "approved"]


class ProjectReviewInput(BaseModel):
    status: ReviewStatus
    functionalityScore: int = Field(ge=0, le=30)
    codeQualityScore: int = Field(ge=0, le=20)
    documentationScore: int = Field(ge=0, le=15)
    integrationScore: int = Field(ge=0, le=20)
    contributionScore: int = Field(ge=0, le=15)
    feedback: str = Field(default="", max_length=4000)

    @field_validator("feedback")
    @classmethod
    def _normalize_feedback(cls, value: str) -> str:
        return value.strip()


class ProjectReviewResponse(ProjectReviewInput):
    projectId: str
    reviewerUsername: str
    totalScore: int = Field(ge=0, le=100)
    updatedAt: str


class ProfessorReviewQueueItem(BaseModel):
    project: ProjectResponse
    review: ProjectReviewResponse | None


class ProfessorReviewQueueResponse(BaseModel):
    totalProjects: int
    pending: int
    inReview: int
    changesRequested: int
    approved: int
    items: list[ProfessorReviewQueueItem]
