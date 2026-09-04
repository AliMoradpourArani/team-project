"""ID-only GitHub connect verifies the username against github.com."""

from __future__ import annotations

import shutil

import httpx
import pytest

from backend.database import source_files
from backend.database.connection import REPOSITORY_ROOT
from backend.database.init_db import initialize_database
from backend.services import github_sync


class _FakeResponse:
    def __init__(self, status_code: int, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"status {self.status_code}",
                request=httpx.Request("GET", "https://api.github.com"),
                response=httpx.Response(self.status_code),
            )

    def json(self):
        return self._payload


class _FakeClient:
    def __init__(self, response=None, error=None):
        self._response = response
        self._error = error
        self.paths: list[str] = []

    def get(self, path, params=None):
        self.paths.append(path)
        if self._error is not None:
            raise self._error
        return self._response


def _client_factory(monkeypatch, response=None, error=None):
    seen: list[_FakeClient] = []

    def factory(token=None, base=None):
        del token, base
        client = _FakeClient(response=response, error=error)
        seen.append(client)
        return client

    monkeypatch.setattr(github_sync, "_new_client", factory)
    return seen


def test_fetch_public_user_returns_canonical_login(monkeypatch):
    _client_factory(monkeypatch, _FakeResponse(200, {"login": "Octocat"}))

    assert github_sync._fetch_public_user("octocat") == "Octocat"


def test_fetch_public_user_rejects_unknown_username(monkeypatch):
    _client_factory(monkeypatch, _FakeResponse(404, {"message": "Not Found"}))

    with pytest.raises(ValueError, match="was not found on github.com"):
        github_sync._fetch_public_user("nobody-here-xyz")


def test_fetch_public_user_fails_closed_when_github_unreachable(monkeypatch):
    _client_factory(monkeypatch, error=httpx.ConnectError("down"))

    with pytest.raises(ValueError, match="Could not reach GitHub"):
        github_sync._fetch_public_user("octocat")


def test_fetch_public_user_reports_rate_limit(monkeypatch):
    _client_factory(monkeypatch, _FakeResponse(403, {"message": "rate limited"}))

    with pytest.raises(ValueError, match="rate limit"):
        github_sync._fetch_public_user("octocat")


def test_connect_github_verifies_id_without_token(tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    shutil.copytree(REPOSITORY_ROOT / "data", data_root)
    monkeypatch.setattr(source_files, "DATA_ROOT", data_root)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    initialize_database(tmp_path / "test.db", seed=True)
    _client_factory(monkeypatch, _FakeResponse(200, {"login": "octocat"}))

    status = github_sync.connect_github("ali", "octocat", None)

    assert status.connected is True
    assert status.username == "octocat"


def test_connect_github_rejects_unknown_id_without_token(tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    shutil.copytree(REPOSITORY_ROOT / "data", data_root)
    monkeypatch.setattr(source_files, "DATA_ROOT", data_root)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    initialize_database(tmp_path / "test.db", seed=True)
    _client_factory(monkeypatch, _FakeResponse(404, {"message": "Not Found"}))

    with pytest.raises(ValueError, match="was not found on github.com"):
        github_sync.connect_github("ali", "ghost-unknown-xyz", None)
    assert github_sync.get_status("ali").connected is False
