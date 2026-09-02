"""Pydantic contracts for the in-app AI project workspace."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .api import ActivityResponse
from .source_data import validate_date_string, validate_slug

AIAction = Literal["plan", "roadmap", "progress", "debug", "review"]
AIFindingSeverity = Literal["info", "warning", "error"]


class AITaskSuggestion(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    date: str
    rationale: str = Field(default="", max_length=600)
    projectId: str | None = None

    @field_validator("date")
    @classmethod
    def _valid_date(cls, value: str) -> str:
        return validate_date_string(value, "AI task date")

    @field_validator("projectId")
    @classmethod
    def _valid_project(cls, value: str | None) -> str | None:
        return validate_slug(value, "project id") if value is not None else None


class AIRoadmapMilestone(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    objective: str = Field(min_length=1, max_length=800)
    targetDate: str
    tasks: list[str] = Field(default_factory=list, max_length=8)

    @field_validator("targetDate")
    @classmethod
    def _valid_date(cls, value: str) -> str:
        return validate_date_string(value, "AI milestone target date")


class AIFinding(BaseModel):
    severity: AIFindingSeverity
    title: str = Field(min_length=1, max_length=180)
    detail: str = Field(min_length=1, max_length=2000)
    recommendation: str = Field(min_length=1, max_length=1200)


class AIWorkspaceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: AIAction
    projectId: str | None = None
    goal: str = Field(default="", max_length=2000)
    taskCount: int = Field(default=5, ge=1, le=12)
    applyTasks: bool = False

    @field_validator("projectId")
    @classmethod
    def _valid_project(cls, value: str | None) -> str | None:
        return validate_slug(value, "project id") if value is not None else None


class AIModelOutput(BaseModel):
    """Provider/local-engine output before server-owned metadata is attached."""

    summary: str = Field(min_length=1, max_length=4000)
    progressPercent: int = Field(ge=0, le=100)
    tasks: list[AITaskSuggestion] = Field(default_factory=list, max_length=12)
    roadmap: list[AIRoadmapMilestone] = Field(default_factory=list, max_length=8)
    findings: list[AIFinding] = Field(default_factory=list, max_length=20)


class AIWorkspaceResponse(AIModelOutput):
    action: AIAction
    provider: str
    model: str | None = None
    providerMessage: str | None = None
    appliedActivities: list[ActivityResponse] = Field(default_factory=list)


class AIStatusResponse(BaseModel):
    available: bool = True
    mode: Literal["provider", "local"]
    provider: str
    model: str | None = None
