"""Read-only GitHub contribution contracts for the professor dashboard."""

from typing import Literal

from pydantic import BaseModel


class GitHubRepositorySummary(BaseModel):
    fullName: str
    url: str
    defaultBranch: str
    openPullRequests: int
    lastPushedAt: str | None = None


class GitHubMemberContribution(BaseModel):
    userId: str
    displayName: str
    githubUsername: str | None = None
    linked: bool
    commits: int
    pullRequests: int
    openPullRequests: int
    mergedPullRequests: int
    latestContributionAt: str | None = None


class GitHubTimelineEvent(BaseModel):
    kind: Literal["commit", "pull-request"]
    userId: str
    githubUsername: str
    title: str
    url: str
    occurredAt: str
    detail: str


class ProfessorGitHubDashboardResponse(BaseModel):
    status: Literal["ok", "unavailable"]
    message: str | None = None
    repository: GitHubRepositorySummary | None = None
    members: list[GitHubMemberContribution]
    timeline: list[GitHubTimelineEvent]
    generatedAt: str
