"""Final-delivery preflight contracts shared by API, UI, and CLI."""

from typing import Literal

from pydantic import BaseModel, Field

from .api import ProjectResponse

PreflightStatus = Literal["ready", "blocked"]


class DeliveryPreflightGate(BaseModel):
    key: str
    label: str
    passed: bool
    blocking: bool = True
    detail: str
    remediation: str


class ProjectDeliveryPreflight(BaseModel):
    project: ProjectResponse
    status: PreflightStatus
    latestSubmissionVersion: int | None
    reviewStatus: str | None
    reviewAfterSubmission: bool
    gates: list[DeliveryPreflightGate]


class DeliveryPreflightResponse(BaseModel):
    status: PreflightStatus
    releaseCandidateReady: bool
    totalProjects: int = Field(ge=0)
    readyProjects: int = Field(ge=0)
    blockingProjects: int = Field(ge=0)
    blockerCount: int = Field(ge=0)
    generatedAt: str
    localCheckCommand: str
    summary: str
    globalGates: list[DeliveryPreflightGate]
    projects: list[ProjectDeliveryPreflight]
