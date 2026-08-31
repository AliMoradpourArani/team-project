"""Pydantic response models for the public API. ISO 8601 for dates."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class UserResponse(BaseModel):
    id: str
    name: str
    role: str


class ActivityResponse(BaseModel):
    id: str
    userId: str
    date: str
    title: str
    status: str
    projectId: str | None = None


class ProjectResponse(BaseModel):
    id: str
    userId: str
    name: str
    description: str
    technology: list[str]
    status: str


class ErrorResponse(BaseModel):
    """Structured error envelope returned for non-2xx API responses."""

    error: str
    detail: str | None = None
