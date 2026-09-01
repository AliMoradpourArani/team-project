from __future__ import annotations

from backend.schemas.api import UserResponse
from backend.services import github_integration


def users():
    return [
        UserResponse(
            id="hossein",
            name="Hossein",
            role="Developer",
            githubUsername="HoosseinRahimi",
        ),
        UserResponse(id="ali", name="Ali", role="Developer", githubUsername=None),
    ]


def payloads():
    repository = {
        "full_name": "HoosseinRahimi/team-project",
        "html_url": "https://github.com/HoosseinRahimi/team-project",
        "default_branch": "main",
        "pushed_at": "2026-09-02T10:00:00Z",
    }
    commits = [
        {
            "sha": "abcdef123456",
            "html_url": "https://github.com/HoosseinRahimi/team-project/commit/abcdef1",
            "author": {"login": "HoosseinRahimi"},
            "commit": {
                "message": "feat: add contribution timeline\n\nbody",
                "author": {"date": "2026-09-02T09:00:00Z"},
                "committer": {"date": "2026-09-02T09:01:00Z"},
            },
        },
        {
            "sha": "deadbeef1234",
            "html_url": "https://github.com/example/commit/deadbee",
            "author": {"login": "SomeoneElse"},
            "commit": {
                "message": "Unrelated commit",
                "author": {"date": "2026-09-02T08:00:00Z"},
            },
        },
    ]
    pulls = [
        {
            "number": 14,
            "title": "Add GitHub integration",
            "html_url": "https://github.com/HoosseinRahimi/team-project/pull/14",
            "state": "closed",
            "merged_at": "2026-09-02T09:30:00Z",
            "closed_at": "2026-09-02T09:30:00Z",
            "created_at": "2026-09-02T08:30:00Z",
            "user": {"login": "HoosseinRahimi"},
        },
        {
            "number": 15,
            "title": "Open follow-up",
            "html_url": "https://github.com/HoosseinRahimi/team-project/pull/15",
            "state": "open",
            "merged_at": None,
            "closed_at": None,
            "created_at": "2026-09-02T09:45:00Z",
            "user": {"login": "HoosseinRahimi"},
        },
    ]
    return repository, commits, pulls


def test_github_dashboard_maps_only_explicitly_linked_members(monkeypatch):
    github_integration.clear_cache()
    monkeypatch.setattr(github_integration.queries, "list_users", users)
    monkeypatch.setattr(github_integration, "_fetch_github_payloads", lambda repository: payloads())
    monkeypatch.setenv("GITHUB_INTEGRATION_ENABLED", "true")
    monkeypatch.setenv("GITHUB_REPOSITORY", "HoosseinRahimi/team-project")

    dashboard = github_integration.get_professor_github_dashboard()

    assert dashboard.status == "ok"
    assert dashboard.repository is not None
    assert dashboard.repository.openPullRequests == 1
    hossein = next(member for member in dashboard.members if member.userId == "hossein")
    ali = next(member for member in dashboard.members if member.userId == "ali")
    assert hossein.commits == 1
    assert hossein.pullRequests == 2
    assert hossein.mergedPullRequests == 1
    assert hossein.openPullRequests == 1
    assert hossein.latestContributionAt == "2026-09-02T09:45:00Z"
    assert ali.linked is False
    assert ali.commits == 0
    assert [event.kind for event in dashboard.timeline] == ["pull-request", "pull-request", "commit"]


def test_github_dashboard_is_offline_safe_when_disabled(monkeypatch):
    github_integration.clear_cache()
    monkeypatch.setattr(github_integration.queries, "list_users", users)
    monkeypatch.setenv("GITHUB_INTEGRATION_ENABLED", "false")

    dashboard = github_integration.get_professor_github_dashboard()

    assert dashboard.status == "unavailable"
    assert dashboard.repository is None
    assert dashboard.members[0].linked is True
    assert dashboard.message == "GitHub integration is disabled for this environment."


def test_github_dashboard_uses_short_lived_cache(monkeypatch):
    github_integration.clear_cache()
    monkeypatch.setattr(github_integration.queries, "list_users", users)
    monkeypatch.setenv("GITHUB_INTEGRATION_ENABLED", "true")
    monkeypatch.setenv("GITHUB_REPOSITORY", "HoosseinRahimi/team-project")
    calls = 0

    def fake_fetch(repository: str):
        nonlocal calls
        calls += 1
        return payloads()

    monkeypatch.setattr(github_integration, "_fetch_github_payloads", fake_fetch)

    first = github_integration.get_professor_github_dashboard()
    second = github_integration.get_professor_github_dashboard()

    assert first == second
    assert calls == 1
