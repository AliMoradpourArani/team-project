"""Validated project manifest and project-integration API contracts."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from .api import ProjectResponse
from .source_data import validate_slug

ProjectType = Literal["cli", "static-web", "api"]
ProjectRunner = Literal["python-script-v1", "static-site-v1", "openapi-json-v1"]
DemoMode = Literal["execute", "preview"]


class ProjectManifest(BaseModel):
    """Git-tracked manifest for one integrated member project."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str = Field(min_length=1)
    owner_id: str
    description: str = Field(min_length=1)
    technology: list[str] = Field(default_factory=list)
    project_type: ProjectType
    runner: ProjectRunner
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

    @model_validator(mode="after")
    def _valid_contract(self) -> ProjectManifest:
        expected = {
            "cli": "python-script-v1",
            "static-web": "static-site-v1",
            "api": "openapi-json-v1",
        }
        expected_runner = expected[self.project_type]
        if self.runner != expected_runner:
            raise ValueError(
                f"project_type {self.project_type!r} requires runner {expected_runner!r}."
            )

        suffix = PurePosixPath(self.entry_point).suffix.lower()
        allowed_suffixes = {
            "python-script-v1": {".py"},
            "static-site-v1": {".html", ".htm"},
            "openapi-json-v1": {".json"},
        }
        if suffix not in allowed_suffixes[self.runner]:
            allowed = ", ".join(sorted(allowed_suffixes[self.runner]))
            raise ValueError(f"{self.runner} entry_point must use one of: {allowed}.")
        return self


class ProjectIntegrationResponse(BaseModel):
    projectId: str
    userId: str
    name: str
    integrationStatus: Literal["ready", "not-integrated", "invalid"]
    runnerEnabled: bool
    runnable: bool
    previewable: bool = False
    demoMode: DemoMode | None = None
    projectType: str | None = None
    runner: str | None = None
    entryPoint: str | None = None
    repositoryPath: str | None = None
    reason: str | None = None


class ProjectHealthCheck(BaseModel):
    key: str
    label: str
    passed: bool
    detail: str


class ProjectPreview(BaseModel):
    kind: Literal["static-html", "openapi-json"]
    content: str
    summary: str
    truncated: bool = False


class ProjectRunHistoryItem(BaseModel):
    id: int
    projectId: str
    runner: str
    exitCode: int | None
    timedOut: bool
    durationMs: int
    stdoutPreview: str
    stderrPreview: str
    outputTruncated: bool
    createdAt: str


class ProjectDetailResponse(BaseModel):
    project: ProjectResponse
    integration: ProjectIntegrationResponse
    health: list[ProjectHealthCheck]
    healthPassed: int
    healthTotal: int
    readme: str | None
    preview: ProjectPreview | None = None
    recentRuns: list[ProjectRunHistoryItem]


class ProjectRunResponse(BaseModel):
    projectId: str
    runner: str
    exitCode: int | None
    timedOut: bool
    durationMs: int
    stdout: str
    stderr: str
    outputTruncated: bool
