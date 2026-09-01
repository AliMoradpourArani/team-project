"""Read-only GitHub contribution aggregation for the professor dashboard."""

from __future__ import annotations

import logging
import os
import re
import threading
import time
from datetime import UTC, datetime
from typing import Any

import httpx

from ..schemas.github import (
    GitHubMemberContribution,
    GitHubRepositorySummary,
    GitHubTimelineEvent,
    ProfessorGitHubDashboardResponse,
)
from . import queries

LOGGER = logging.getLogger(__name__)
GITHUB_API_BASE_URL = "https://api.github.com"
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_CACHE_LOCK = threading.Lock()
_CACHE: dict[str, tuple[float, ProfessorGitHubDashboardResponse]] = {}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _enabled() -> bool:
    return os.getenv("GITHUB_INTEGRATION_ENABLED", "true").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def _repository_name() -> str:
    repository = os.getenv("GITHUB_REPOSITORY", "HoosseinRahimi/team-project").strip()
    if not REPOSITORY_PATTERN.fullmatch(repository):
        raise ValueError("GITHUB_REPOSITORY must use the owner/repository form.")
    return repository


def _cache_ttl_seconds() -> float:
    try:
        value = float(os.getenv("GITHUB_CACHE_TTL_SECONDS", "60"))
    except ValueError:
        value = 60.0
    return min(max(value, 10.0), 3600.0)


def _timeout_seconds() -> float:
    try:
        value = float(os.getenv("GITHUB_API_TIMEOUT_SECONDS", "5"))
    except ValueError:
        value = 5.0
    return min(max(value, 1.0), 30.0)


def _headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "team-project-professor-dashboard",
    }
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _fetch_github_payloads(repository: str) -> tuple[dict[str, Any], list[Any], list[Any]]:
    """Fetch one repository snapshot, recent default-branch commits, and recent PRs."""
    with httpx.Client(
        base_url=GITHUB_API_BASE_URL,
        headers=_headers(),
        timeout=_timeout_seconds(),
        follow_redirects=False,
    ) as client:
        repo_response = client.get(f"/repos/{repository}")
        repo_response.raise_for_status()
        commits_response = client.get(f"/repos/{repository}/commits", params={"per_page": 100})
        commits_response.raise_for_status()
        pulls_response = client.get(
            f"/repos/{repository}/pulls",
            params={"state": "all", "sort": "updated", "direction": "desc", "per_page": 100},
        )
        pulls_response.raise_for_status()
        return repo_response.json(), commits_response.json(), pulls_response.json()


def _member_shells() -> list[GitHubMemberContribution]:
    return [
        GitHubMemberContribution(
            userId=user.id,
            displayName=user.name,
            githubUsername=user.githubUsername,
            linked=user.githubUsername is not None,
            commits=0,
            pullRequests=0,
            openPullRequests=0,
            mergedPullRequests=0,
            latestContributionAt=None,
        )
        for user in queries.list_users()
    ]


def _event_time_for_pull(pull: dict[str, Any]) -> str | None:
    return pull.get("merged_at") or pull.get("closed_at") or pull.get("created_at")


def _build_dashboard(
    repository: str,
    repo_payload: dict[str, Any],
    commits_payload: list[Any],
    pulls_payload: list[Any],
) -> ProfessorGitHubDashboardResponse:
    members = _member_shells()
    by_login = {
        member.githubUsername.lower(): member
        for member in members
        if member.githubUsername is not None
    }
    latest_by_user: dict[str, list[str]] = {member.userId: [] for member in members}
    timeline: list[GitHubTimelineEvent] = []

    for item in commits_payload:
        author = item.get("author") or {}
        login = author.get("login")
        if not isinstance(login, str):
            continue
        member = by_login.get(login.lower())
        if member is None:
            continue
        commit = item.get("commit") or {}
        author_info = commit.get("author") or {}
        timestamp = author_info.get("date") or (commit.get("committer") or {}).get("date")
        if not isinstance(timestamp, str):
            continue
        message = str(commit.get("message") or "Commit").splitlines()[0][:160]
        member.commits += 1
        latest_by_user[member.userId].append(timestamp)
        timeline.append(
            GitHubTimelineEvent(
                kind="commit",
                userId=member.userId,
                githubUsername=login,
                title=message,
                url=str(item.get("html_url") or ""),
                occurredAt=timestamp,
                detail=f"commit {str(item.get('sha') or '')[:7]}",
            )
        )

    for pull in pulls_payload:
        author = pull.get("user") or {}
        login = author.get("login")
        if not isinstance(login, str):
            continue
        member = by_login.get(login.lower())
        if member is None:
            continue
        timestamp = _event_time_for_pull(pull)
        if not isinstance(timestamp, str):
            continue
        merged = pull.get("merged_at") is not None
        state = str(pull.get("state") or "unknown")
        member.pullRequests += 1
        member.openPullRequests += state == "open"
        member.mergedPullRequests += merged
        latest_by_user[member.userId].append(timestamp)
        detail = "merged PR" if merged else f"{state} PR"
        timeline.append(
            GitHubTimelineEvent(
                kind="pull-request",
                userId=member.userId,
                githubUsername=login,
                title=f"#{pull.get('number')} {pull.get('title') or 'Pull request'}",
                url=str(pull.get("html_url") or ""),
                occurredAt=timestamp,
                detail=detail,
            )
        )

    for member in members:
        timestamps = latest_by_user[member.userId]
        member.latestContributionAt = max(timestamps) if timestamps else None

    timeline.sort(key=lambda event: (event.occurredAt, event.title), reverse=True)
    repository_summary = GitHubRepositorySummary(
        fullName=str(repo_payload.get("full_name") or repository),
        url=str(repo_payload.get("html_url") or f"https://github.com/{repository}"),
        defaultBranch=str(repo_payload.get("default_branch") or "main"),
        openPullRequests=sum(pull.get("state") == "open" for pull in pulls_payload),
        lastPushedAt=repo_payload.get("pushed_at"),
    )
    return ProfessorGitHubDashboardResponse(
        status="ok",
        repository=repository_summary,
        members=members,
        timeline=timeline[:20],
        generatedAt=_utc_now(),
    )


def _unavailable(message: str) -> ProfessorGitHubDashboardResponse:
    return ProfessorGitHubDashboardResponse(
        status="unavailable",
        message=message,
        members=_member_shells(),
        timeline=[],
        generatedAt=_utc_now(),
    )


def clear_cache() -> None:
    """Clear the in-process read cache, primarily for tests and local debugging."""
    with _CACHE_LOCK:
        _CACHE.clear()


def get_professor_github_dashboard() -> ProfessorGitHubDashboardResponse:
    """Return a cached, read-only GitHub contribution snapshot for the configured repo."""
    if not _enabled():
        return _unavailable("GitHub integration is disabled for this environment.")

    try:
        repository = _repository_name()
    except ValueError:
        LOGGER.exception("Invalid GitHub repository configuration")
        return _unavailable("GitHub integration is not configured correctly.")

    cache_key = repository.lower()
    now = time.monotonic()
    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached is not None and cached[0] > now:
            return cached[1]

    try:
        repo_payload, commits_payload, pulls_payload = _fetch_github_payloads(repository)
        dashboard = _build_dashboard(repository, repo_payload, commits_payload, pulls_payload)
    except (httpx.HTTPError, TypeError, ValueError):
        LOGGER.exception("GitHub contribution refresh failed for %s", repository)
        return _unavailable("GitHub contribution data is temporarily unavailable.")

    with _CACHE_LOCK:
        _CACHE[cache_key] = (now + _cache_ttl_seconds(), dashboard)
    return dashboard
