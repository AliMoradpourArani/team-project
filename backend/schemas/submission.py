"""Immutable project submission and professor release contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from .api import ProjectResponse
from .project_review import ProjectReviewResponse


class SubmissionSettingsInput(BaseModel):
    isOpen: bool
    deadlineAt: datetime | None = None

    @field_validator("deadlineAt")
    @classmethod
    def _require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("deadlineAt must include a timezone offset.")
        return value


class SubmissionSettingsResponse(BaseModel):
    isOpen: bool
    deadlineAt: str | None
    acceptingSubmissions: bool
    updatedByUsername: str | None
    updatedAt: str


class ProjectSubmissionResponse(BaseModel):
    id: int
    projectId: str
    userId: str
    submittedByUsername: str
    version: int = Field(gt=0)
    snapshotDigest: str = Field(min_length=64, max_length=64)
    sourceFileCount: int = Field(ge=0)
    sourceTotalBytes: int = Field(ge=0)
    reviewStatus: str | None
    reviewTotalScore: int | None = Field(default=None, ge=0, le=100)
    submittedAt: str


class ProjectSubmissionStatusResponse(BaseModel):
    settings: SubmissionSettingsResponse
    latestSubmission: ProjectSubmissionResponse | None
    historyCount: int = Field(ge=0)
    canSubmit: bool
    blockedReason: str | None


class ProfessorSubmissionItem(BaseModel):
    project: ProjectResponse
    latestSubmission: ProjectSubmissionResponse | None
    review: ProjectReviewResponse | None


class ProfessorSubmissionDashboardResponse(BaseModel):
    settings: SubmissionSettingsResponse
    totalProjects: int = Field(ge=0)
    submittedProjects: int = Field(ge=0)
    pendingProjects: int = Field(ge=0)
    approvedProjects: int = Field(ge=0)
    releaseReady: bool
    releaseBlockedReason: str | None
    items: list[ProfessorSubmissionItem]


class SubmissionReleaseInput(BaseModel):
    label: str = Field(min_length=1, max_length=120)

    @field_validator("label")
    @classmethod
    def _normalize_label(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("Release label cannot be empty.")
        return normalized


class SubmissionReleaseSummary(BaseModel):
    id: int
    label: str
    manifestDigest: str = Field(min_length=64, max_length=64)
    projectCount: int = Field(gt=0)
    createdByUsername: str
    createdAt: str


class SubmissionReleaseDetail(SubmissionReleaseSummary):
    manifest: dict
