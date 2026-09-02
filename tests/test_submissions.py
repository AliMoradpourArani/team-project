"""Phase 9 submission and frozen release API tests."""

from __future__ import annotations

import shutil

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.database import source_files
from backend.database.connection import REPOSITORY_ROOT, connect
from backend.database.init_db import initialize_database
from backend.services import submissions
from backend.services.auth import create_or_update_account

STUDENT_PASSWORD = "student-pass-123"
PROFESSOR_PASSWORD = "professor-pass-123"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    shutil.copytree(REPOSITORY_ROOT / "data", data_root)
    monkeypatch.setattr(source_files, "DATA_ROOT", data_root)

    projects_root = tmp_path / "projects"
    shutil.copytree(REPOSITORY_ROOT / "projects", projects_root)
    monkeypatch.setattr(submissions, "REPOSITORY_ROOT", tmp_path)

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


def approved_review_payload():
    return {
        "status": "approved",
        "functionalityScore": 28,
        "codeQualityScore": 18,
        "documentationScore": 13,
        "integrationScore": 19,
        "contributionScore": 14,
        "feedback": "Approved for final submission.",
    }


def test_student_creates_immutable_versioned_submissions(client):
    csrf = login(client, "hossein", STUDENT_PASSWORD)

    initial = client.get("/api/projects/team-foundation/submission")
    assert initial.status_code == 200
    assert initial.json()["canSubmit"] is True
    assert initial.json()["latestSubmission"] is None
    assert client.post("/api/projects/team-foundation/submit").status_code == 403

    first = client.post(
        "/api/projects/team-foundation/submit",
        headers={"X-CSRF-Token": csrf},
    )
    assert first.status_code == 200
    first_body = first.json()
    assert first_body["version"] == 1
    assert len(first_body["snapshotDigest"]) == 64
    assert first_body["sourceFileCount"] > 0
    assert first_body["sourceTotalBytes"] > 0

    second = client.post(
        "/api/projects/team-foundation/submit",
        headers={"X-CSRF-Token": csrf},
    )
    assert second.status_code == 200
    assert second.json()["version"] == 2
    assert second.json()["snapshotDigest"] == first_body["snapshotDigest"]

    status = client.get("/api/projects/team-foundation/submission").json()
    assert status["historyCount"] == 2
    assert status["latestSubmission"]["version"] == 2

    professor_csrf = login(client, "professor", PROFESSOR_PASSWORD)
    assert (
        client.post(
            "/api/projects/team-foundation/submit",
            headers={"X-CSRF-Token": professor_csrf},
        ).status_code
        == 403
    )


def test_submission_rejects_likely_secret_files(client, tmp_path):
    project_dir = tmp_path / "projects" / "hossein" / "team-platform"
    secret = project_dir / ".env.local"
    secret.write_text("TOKEN=do-not-snapshot\n", encoding="utf-8")

    csrf = login(client, "hossein", STUDENT_PASSWORD)
    response = client.post(
        "/api/projects/team-foundation/submit",
        headers={"X-CSRF-Token": csrf},
    )

    assert response.status_code == 409
    assert "Potential secret file" in response.json()["detail"]
    assert client.get("/api/projects/team-foundation/submission").json()["historyCount"] == 0


def test_professor_controls_submission_window_and_deadline_validation(client):
    professor_csrf = login(client, "professor", PROFESSOR_PASSWORD)

    assert (
        client.put(
            "/api/professor/submission-settings",
            json={"isOpen": False, "deadlineAt": None},
        ).status_code
        == 403
    )
    closed = client.put(
        "/api/professor/submission-settings",
        json={"isOpen": False, "deadlineAt": None},
        headers={"X-CSRF-Token": professor_csrf},
    )
    assert closed.status_code == 200
    assert closed.json()["acceptingSubmissions"] is False

    student_csrf = login(client, "hossein", STUDENT_PASSWORD)
    status = client.get("/api/projects/team-foundation/submission").json()
    assert status["canSubmit"] is False
    assert "closed" in status["blockedReason"].lower()
    blocked = client.post(
        "/api/projects/team-foundation/submit",
        headers={"X-CSRF-Token": student_csrf},
    )
    assert blocked.status_code == 409

    professor_csrf = login(client, "professor", PROFESSOR_PASSWORD)
    naive_deadline = client.put(
        "/api/professor/submission-settings",
        json={"isOpen": True, "deadlineAt": "2026-09-10T12:00:00"},
        headers={"X-CSRF-Token": professor_csrf},
    )
    assert naive_deadline.status_code == 422


def test_professor_freezes_release_only_after_every_project_is_submitted_and_approved(client):
    professor_csrf = login(client, "professor", PROFESSOR_PASSWORD)

    initial = client.get("/api/professor/submissions")
    assert initial.status_code == 200
    assert initial.json()["releaseReady"] is False
    blocked = client.post(
        "/api/professor/releases",
        json={"label": "Final submission"},
        headers={"X-CSRF-Token": professor_csrf},
    )
    assert blocked.status_code == 409

    for project_id in ("team-foundation", "ali-sample-project", "reza-sample-project"):
        review = client.put(
            f"/api/projects/{project_id}/review",
            json=approved_review_payload(),
            headers={"X-CSRF-Token": professor_csrf},
        )
        assert review.status_code == 200

    student_csrf = login(client, "hossein", STUDENT_PASSWORD)
    submitted = client.post(
        "/api/projects/team-foundation/submit",
        headers={"X-CSRF-Token": student_csrf},
    )
    assert submitted.status_code == 200

    with connect() as connection, connection:
        for user_id, project_id, marker in (
            ("ali", "ali-sample-project", "b"),
            ("reza", "reza-sample-project", "c"),
        ):
            account = connection.execute(
                "SELECT id FROM auth_accounts WHERE username = ?", (user_id,)
            ).fetchone()
            connection.execute(
                """
                INSERT INTO project_submissions (
                    project_id, user_id, submitted_by_account_id, version, snapshot_digest,
                    source_file_count, source_total_bytes, review_status, review_total_score, snapshot_json
                ) VALUES (?, ?, ?, 1, ?, 1, 10, 'approved', 92, '{}')
                """,
                (project_id, user_id, account["id"], marker * 64),
            )

    professor_csrf = login(client, "professor", PROFESSOR_PASSWORD)
    dashboard = client.get("/api/professor/submissions").json()
    assert dashboard["submittedProjects"] == 3
    assert dashboard["approvedProjects"] == 3
    assert dashboard["releaseReady"] is True

    release = client.post(
        "/api/professor/releases",
        json={"label": "Final submission"},
        headers={"X-CSRF-Token": professor_csrf},
    )
    assert release.status_code == 200
    body = release.json()
    assert body["projectCount"] == 3
    assert len(body["manifestDigest"]) == 64
    assert len(body["manifest"]["projects"]) == 3

    duplicate = client.post(
        "/api/professor/releases",
        json={"label": "Final submission"},
        headers={"X-CSRF-Token": professor_csrf},
    )
    assert duplicate.status_code == 409
    assert len(client.get("/api/professor/releases").json()) == 1

    login(client, "hossein", STUDENT_PASSWORD)
    assert client.get("/api/professor/submissions").status_code == 403
    assert client.get("/api/professor/releases").status_code == 403
