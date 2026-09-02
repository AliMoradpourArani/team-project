"""Phase 11 final-delivery preflight and release-candidate gate tests."""

from __future__ import annotations

import shutil
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.database import source_files
from backend.database.connection import REPOSITORY_ROOT
from backend.database.init_db import initialize_database
from backend.services import delivery_preflight, delivery_rules, submissions
from backend.services.auth import create_or_update_account

STUDENT_PASSWORD = "student-pass-123"
PROFESSOR_PASSWORD = "professor-pass-123"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    shutil.copytree(REPOSITORY_ROOT / "data", data_root)
    monkeypatch.setattr(source_files, "DATA_ROOT", data_root)

    database_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(database_path))
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("GITHUB_INTEGRATION_ENABLED", "false")
    initialize_database(database_path, seed=True)
    for user_id in ("hossein", "ali", "reza"):
        create_or_update_account(
            username=user_id,
            password=STUDENT_PASSWORD,
            role="student",
            user_id=user_id,
        )
    create_or_update_account(
        username="professor", password=PROFESSOR_PASSWORD, role="professor"
    )
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["csrfToken"]


def test_professor_preflight_reports_real_blockers_without_mutating_state(client):
    login(client, "professor", PROFESSOR_PASSWORD)

    response = client.get("/api/professor/preflight")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "blocked"
    assert body["releaseCandidateReady"] is False
    assert body["totalProjects"] == 3
    assert body["blockerCount"] > 0
    assert body["localCheckCommand"] == "make delivery-preflight"
    gates = {gate["key"]: gate for gate in body["globalGates"]}
    assert gates["runtime-accounts"]["passed"] is True
    assert gates["all-integrated"]["passed"] is False
    projects = {item["project"]["id"]: item for item in body["projects"]}
    assert projects["team-foundation"]["latestSubmissionVersion"] is None
    assert projects["ali-sample-project"]["status"] == "blocked"
    assert projects["reza-sample-project"]["status"] == "blocked"


def test_preflight_is_professor_only(client):
    login(client, "hossein", STUDENT_PASSWORD)
    assert client.get("/api/professor/preflight").status_code == 403


def test_final_approval_must_follow_latest_frozen_submission():
    submission = SimpleNamespace(submittedAt="2026-09-02 10:00:00")
    earlier_review = SimpleNamespace(status="approved", updatedAt="2026-09-02 09:59:59")
    later_review = SimpleNamespace(status="approved", updatedAt="2026-09-02 10:00:01")
    changes_requested = SimpleNamespace(status="changes-requested", updatedAt="2026-09-02 10:00:02")

    assert delivery_rules.review_covers_submission(earlier_review, submission) is False
    assert delivery_rules.review_covers_submission(later_review, submission) is True
    assert delivery_rules.review_covers_submission(changes_requested, submission) is False
    assert delivery_rules.review_covers_submission(None, submission) is False


def test_release_endpoint_refuses_to_bypass_preflight(client, monkeypatch):
    professor_csrf = login(client, "professor", PROFESSOR_PASSWORD)
    monkeypatch.setattr(
        delivery_preflight,
        "get_delivery_preflight",
        lambda projects: SimpleNamespace(
            releaseCandidateReady=False,
            summary="BLOCKED: final approval must follow freeze",
        ),
    )

    def should_not_run(*args, **kwargs):
        raise AssertionError("submissions.create_release must not run when preflight is blocked")

    monkeypatch.setattr(submissions, "create_release", should_not_run)
    response = client.post(
        "/api/professor/releases",
        json={"label": "RC1"},
        headers={"X-CSRF-Token": professor_csrf},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "BLOCKED: final approval must follow freeze"
