"""Contracts for repository intelligence, governed actions, health, and autonomy."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .api import ActivityResponse
from .source_data import validate_slug

AIActionKind = Literal[
    "create-task",
    "update-progress",
    "record-decision",
    "link-github",
    "github-branch",
    "github-issue",
    "github-pull-request",
]
AIActionStatus = Literal["pending", "approved", "executed", "rejected", "blocked", "failed"]


class AIRepoIndexResponse(BaseModel):
    projectId: str | None
    filesIndexed: int = Field(ge=0)
    chunksIndexed: int = Field(ge=0)
    skippedFiles: int = Field(ge=0)


class AIRagQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query: str = Field(min_length=2, max_length=2000)
    topK: int = Field(default=8, ge=1, le=20)


class AIRagHit(BaseModel):
    path: str
    chunkIndex: int = Field(ge=0)
    score: float = Field(ge=0)
    excerpt: str


class AIRagResponse(BaseModel):
    projectId: str | None
    query: str
    retrievalMode: Literal["lexical-rag"] = "lexical-rag"
    hits: list[AIRagHit] = Field(default_factory=list, max_length=20)


class AIActionProposalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    projectId: str | None = None
    kind: AIActionKind
    payload: dict[str, object] = Field(default_factory=dict)

    @field_validator("projectId")
    @classmethod
    def _valid_project(cls, value: str | None) -> str | None:
        return validate_slug(value, "project id") if value is not None else None


class AIActionRecord(BaseModel):
    id: int
    projectId: str | None
    kind: AIActionKind
    payload: dict[str, object]
    status: AIActionStatus
    result: dict[str, object] | None = None
    createdAt: str
    approvedAt: str | None = None
    executedAt: str | None = None


class AIProgressSyncRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    projectId: str | None = None
    apply: bool = False

    @field_validator("projectId")
    @classmethod
    def _valid_project(cls, value: str | None) -> str | None:
        return validate_slug(value, "project id") if value is not None else None


class AIProgressChange(BaseModel):
    activityId: str
    fromStatus: str
    toStatus: str
    reason: str
    applied: bool


class AIProgressSyncResponse(BaseModel):
    projectId: str | None
    changes: list[AIProgressChange] = Field(default_factory=list)
    updatedActivities: list[ActivityResponse] = Field(default_factory=list)


class AIWeeklyBrief(BaseModel):
    projectId: str | None
    headline: str
    progressPercent: int = Field(ge=0, le=100)
    healthScore: int = Field(ge=0, le=100)
    completedTasks: int = Field(ge=0)
    inProgressTasks: int = Field(ge=0)
    overdueTasks: int = Field(ge=0)
    githubSignals: int = Field(ge=0)
    risks: list[str] = Field(default_factory=list, max_length=10)
    nextWeek: list[str] = Field(default_factory=list, max_length=10)


class AIHealthScore(BaseModel):
    projectId: str | None
    overall: int = Field(ge=0, le=100)
    delivery: int = Field(ge=0, le=100)
    code: int = Field(ge=0, le=100)
    security: int = Field(ge=0, le=100)
    tests: int = Field(ge=0, le=100)
    schedule: int = Field(ge=0, le=100)
    documentation: int = Field(ge=0, le=100)
    reasons: list[str] = Field(default_factory=list, max_length=12)


class AIDebugRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    projectId: str | None = None
    logs: str = Field(min_length=1, max_length=12000)

    @field_validator("projectId")
    @classmethod
    def _valid_project(cls, value: str | None) -> str | None:
        return validate_slug(value, "project id") if value is not None else None


class AIDebugResponse(BaseModel):
    projectId: str | None
    summary: str
    suspectedFiles: list[AIRagHit] = Field(default_factory=list, max_length=12)
    recommendations: list[str] = Field(default_factory=list, max_length=12)


class AIMemorySearchResponse(BaseModel):
    projectId: str | None
    query: str
    matches: list[str] = Field(default_factory=list, max_length=20)


class AIOrchestrationResponse(BaseModel):
    projectId: str | None
    executiveSummary: str
    consensus: list[str] = Field(default_factory=list, max_length=12)
    disagreements: list[str] = Field(default_factory=list, max_length=12)
    nextActions: list[str] = Field(default_factory=list, max_length=12)


class AINotification(BaseModel):
    id: int
    projectId: str | None
    severity: Literal["info", "warning", "error"]
    title: str
    detail: str
    readAt: str | None = None
    createdAt: str
