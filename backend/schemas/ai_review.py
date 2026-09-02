"""Contracts for diff-aware AI code review."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .ai import AIFinding
from .ai_autonomy import AIRagHit
from .source_data import validate_slug


class AICodeReviewRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    projectId: str | None = None
    diff: str = Field(min_length=1, max_length=50000)

    @field_validator("projectId")
    @classmethod
    def _valid_project(cls, value: str | None) -> str | None:
        return validate_slug(value, "project id") if value is not None else None


class AICodeReviewResponse(BaseModel):
    summary: str
    findings: list[AIFinding] = Field(default_factory=list, max_length=30)
    context: list[AIRagHit] = Field(default_factory=list, max_length=12)
