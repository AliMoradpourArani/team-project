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


def create_thread(client: TestClient, csrf: str) -> str:
    response = client.post(
        "/api/ai/threads",
        json={"projectId": "team-foundation", "title": "Release agent"},
        headers={"X-CSRF-Token": csrf},
    )
    assert response.status_code == 201
    return response.json()["id"]


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


def test_student_agent_thread_persists_messages_and_memory(client):
    csrf = login(client, "hossein", STUDENT_PASSWORD)
    thread_id = create_thread(client, csrf)

    message_response = client.post(
        f"/api/ai/threads/{thread_id}/messages",
        json={"content": "Replan my work and check current blockers"},
        headers={"X-CSRF-Token": csrf},
    )
    assert message_response.status_code == 200
    body = message_response.json()
    assert body["thread"]["projectId"] == "team-foundation"
    assert len(body["thread"]["messages"]) == 2
    assert body["thread"]["memory"]
    assert body["snapshot"]["progressPercent"] >= 0
    assert body["provider"] == "local"

    listed = client.get("/api/ai/threads")
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == thread_id
    assert len(listed.json()[0]["messages"]) == 2

    snapshot = client.get(f"/api/ai/threads/{thread_id}/snapshot")
    assert snapshot.status_code == 200
    assert snapshot.json()["progressPercent"] >= 0


def test_agent_thread_requires_csrf_and_owned_project(client):
    csrf = login(client, "hossein", STUDENT_PASSWORD)
    assert (
        client.post(
            "/api/ai/threads",
            json={"projectId": "team-foundation", "title": "No csrf"},
        ).status_code
        == 403
    )
    forbidden = client.post(
        "/api/ai/threads",
        json={"projectId": "ali-sample-project", "title": "Foreign project"},
        headers={"X-CSRF-Token": csrf},
    )
    assert forbidden.status_code == 404


def test_professor_cannot_read_student_agent_threads(client):
    login(client, "professor", PROFESSOR_PASSWORD)
    assert client.get("/api/ai/threads").status_code == 403


def test_agent_replan_has_preview_and_explicit_apply(client):
    csrf = login(client, "hossein", STUDENT_PASSWORD)
    thread_id = create_thread(client, csrf)

    preview = client.post(
        f"/api/ai/threads/{thread_id}/replan",
        json={"applyTasks": False, "taskCount": 2},
        headers={"X-CSRF-Token": csrf},
    )
    assert preview.status_code == 200
    assert len(preview.json()["tasks"]) == 2
    assert preview.json()["appliedActivities"] == []

    applied = client.post(
        f"/api/ai/threads/{thread_id}/replan",
        json={"applyTasks": True, "taskCount": 2},
        headers={"X-CSRF-Token": csrf},
    )
    assert applied.status_code == 200
    assert len(applied.json()["appliedActivities"]) == 2
    assert all(item["projectId"] == "team-foundation" for item in applied.json()["appliedActivities"])


def test_project_memory_is_structured_and_scoped(client):
    csrf = login(client, "hossein", STUDENT_PASSWORD)
    saved = client.put(
        "/api/ai/memory?projectId=team-foundation",
        json={"key": "definition-of-done", "value": "Tests green, docs current, PR reviewed"},
        headers={"X-CSRF-Token": csrf},
    )
    assert saved.status_code == 200
    assert saved.json()["key"] == "definition-of-done"

    listed = client.get("/api/ai/memory?projectId=team-foundation")
    assert listed.status_code == 200
    assert listed.json()[0]["value"] == "Tests green, docs current, PR reviewed"

    foreign = client.get("/api/ai/memory?projectId=ali-sample-project")
    assert foreign.status_code == 404


def test_daily_brief_and_multi_agent_review_are_grounded(client):
    login(client, "hossein", STUDENT_PASSWORD)
    brief = client.get("/api/ai/brief?projectId=team-foundation")
    assert brief.status_code == 200
    assert brief.json()["projectId"] == "team-foundation"
    assert 0 <= brief.json()["progressPercent"] <= 100

    review = client.get("/api/ai/multi-agent-review?projectId=team-foundation")
    assert review.status_code == 200
    assert len(review.json()["results"]) == 7
    assert {item["specialist"] for item in review.json()["results"]} == {
        "planner",
        "project-manager",
        "code-reviewer",
        "debugger",
        "progress-tracker",
        "github-agent",
        "documentation-agent",
    }


def test_activity_can_be_linked_to_github_evidence(client):
    csrf = login(client, "hossein", STUDENT_PASSWORD)
    payload = {
        "activityId": "hossein-2026-08-31-init-repository",
        "kind": "pull-request",
        "reference": "https://github.com/HoosseinRahimi/team-project/pull/30",
    }
    created = client.post(
        "/api/ai/github-links?projectId=team-foundation",
        json=payload,
        headers={"X-CSRF-Token": csrf},
    )
    assert created.status_code == 201
    assert created.json()["kind"] == "pull-request"

    links = client.get("/api/ai/github-links?projectId=team-foundation")
    assert links.status_code == 200
    assert links.json()[0]["activityId"] == payload["activityId"]
