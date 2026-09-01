"""Validated project manifest and runner API contracts."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .source_data import validate_slug


class ProjectManifest(BaseModel):
    """Git-tracked manifest for one integrated member project."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1)
    owner_id: str
    description: str = Field(min_length=1)
    technology: list[str] = Field(default_factory=list)
    project_type: Literal["cli"]
    runner: Literal["python-script-v1"]
    entry_point: str
    repository_path: str

    @field_validator("id")
    @classmethod
    def _valid_id(cls, value: str) -> str:
        return validate_slug(value, "project manifest id")

    @field_validator("owner_id")
    @classmethod
    def _valid_owner(cls, value: str) -> str:
        return validate_slug(value, "project manifest owner id")

    @field_validator("entry_point")
    @classmethod
    def _valid_entry_point(cls, value: str) -> str:
        path = PurePosixPath(value)
        if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError("entry_point must be a clean relative path inside the project directory.")
        if path.suffix.lower() != ".py":
            raise ValueError("python-script-v1 entry_point must point to a .py file.")
        return path.as_posix()

    @field_validator("repository_path")
    @classmethod
    def _valid_repository_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if path.is_absolute() or len(path.parts) != 3 or path.parts[0] != "projects":
            raise ValueError("repository_path must be projects/<owner>/<project-directory>.")
        if any(part in {"", ".", ".."} for part in path.parts):
            raise ValueError("repository_path must not contain traversal segments.")
        validate_slug(path.parts[1], "project repository owner directory")
        validate_slug(path.parts[2], "project repository directory")
        return path.as_posix()


class ProjectIntegrationResponse(BaseModel):
    projectId: str
    userId: str
    name: str
    integrationStatus: Literal["ready", "not-integrated", "invalid"]
    runnerEnabled: bool
    runnable: bool
    projectType: str | None = None
    runner: str | None = None
    entryPoint: str | None = None
    repositoryPath: str | None = None
    reason: str | None = None


class ProjectRunResponse(BaseModel):
    projectId: str
    runner: str
    exitCode: int | None
    timedOut: bool
    durationMs: int
    stdout: str
    stderr: str
    outputTruncated: bool
