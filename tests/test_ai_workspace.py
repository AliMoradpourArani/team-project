"""Coverage for the authenticated in-app AI workspace."""

from __future__ import annotations

import shutil

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.database import source_files
from backend.database.connection import REPOSITORY_ROOT
from backend.database.init_db import initialize_database
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
    monkeypatch.delenv("AI_API_KEY", raising=False)
    initialize_database(database_path, seed=True)
    create_or_update_account(
        username="hossein", password=STUDENT_PASSWORD, role="student", user_id="hossein"
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


def test_ai_status_requires_auth_and_supports_local_mode(client):
    assert client.get("/api/ai/status").status_code == 401
    login(client, "hossein", STUDENT_PASSWORD)
    response = client.get("/api/ai/status")
    assert response.status_code == 200
    assert response.json() == {
        "available": True,
        "mode": "local",
        "provider": "local",
        "model": None,
    }


def test_student_can_generate_and_apply_ai_tasks(client):
    csrf = login(client, "hossein", STUDENT_PASSWORD)
    payload = {
        "action": "plan",
        "projectId": "team-foundation",
        "goal": "Finish the next stable release",
        "taskCount": 3,
        "applyTasks": True,
    }

    assert client.post("/api/ai/workspace", json=payload).status_code == 403

    response = client.post(
        "/api/ai/workspace",
        json=payload,
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "local"
    assert body["action"] == "plan"
    assert len(body["tasks"]) == 3
    assert len(body["appliedActivities"]) == 3
    assert all(item["userId"] == "hossein" for item in body["appliedActivities"])
    assert all(item["projectId"] == "team-foundation" for item in body["appliedActivities"])

    activities = client.get("/api/activities").json()
    generated_ids = {item["id"] for item in body["appliedActivities"]}
    assert generated_ids.issubset({item["id"] for item in activities})


def test_ai_cannot_access_another_students_project(client):
    csrf = login(client, "hossein", STUDENT_PASSWORD)
    response = client.post(
        "/api/ai/workspace",
        json={
            "action": "review",
            "projectId": "ali-sample-project",
            "goal": "Review this project",
            "taskCount": 3,
            "applyTasks": False,
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 404


def test_professor_cannot_mutate_student_ai_workspace(client):
    csrf = login(client, "professor", PROFESSOR_PASSWORD)
    response = client.post(
        "/api/ai/workspace",
        json={
            "action": "plan",
            "projectId": None,
            "goal": "Create student tasks",
            "taskCount": 2,
            "applyTasks": True,
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 403
