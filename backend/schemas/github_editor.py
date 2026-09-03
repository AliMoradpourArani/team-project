"""API contracts for the student GitHub sync and in-page code editor feature."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .api import ProjectResponse
from .source_data import validate_github_username


class GithubStatus(BaseModel):
    """Connection state returned by GitHub status / connect endpoints."""

    connected: bool
    username: str | None = None
    syncedAt: str | None = None
    canPush: bool = False
    avatarUrl: str | None = None


class GithubConnectInput(BaseModel):
    """Payload used to connect a student GitHub account."""

    model_config = ConfigDict(extra="forbid")

    username: str = Field(min_length=1)
    token: str | None = None

    @field_validator("username")
    @classmethod
    def _valid_username(cls, value: str) -> str:
        return validate_github_username(value)


class GithubRepo(BaseModel):
    """One GitHub repository surfaced in the student's repository picker."""

    fullName: str
    name: str
    owner: str
    htmlUrl: str
    language: str | None = None
    defaultBranch: str = "main"
    updatedAt: str | None = None
    private: bool = False


class GithubImportInput(BaseModel):
    """Payload requesting an import of an owned repository."""

    model_config = ConfigDict(extra="forbid")

    fullName: str = Field(min_length=1)


class GithubImportResponse(BaseModel):
    """Outcome of importing a repository into the student workspace."""

    project: ProjectResponse
    imported: bool
    repositoryPath: str
    entryPoint: str


class ProjectFileEntry(BaseModel):
    """One path entry in a recursive project file listing."""

    path: str
    name: str
    isDirectory: bool
    size: int = 0


class ProjectFilePayload(BaseModel):
    """Payload used to write a project file."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    content: str


class ProjectFileResponse(BaseModel):
    """File content returned for reads and writes."""

    path: str
    content: str
    size: int


class ProjectCommitInput(BaseModel):
    """Payload used to commit project changes to its git remote."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=500)


class ProjectCommitResponse(BaseModel):
    """Outcome of a commit + push attempt for a project."""

    committed: bool
    pushed: bool = False
    message: str
    sha: str | None = None
    detail: str
    kind: Literal["commit", "error"] = "commit"
