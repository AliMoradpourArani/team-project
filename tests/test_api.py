"""API tests for authenticated student and professor flows."""

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


def test_health_remains_public(client):
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/health").json() == {"status": "ok"}


def test_protected_api_requires_authentication(client):
    for path in ["/api/users", "/api/activities", "/api/projects", "/api/professor/dashboard"]:
        assert client.get(path).status_code == 401


def test_invalid_login_is_generic(client):
    response = client.post(
        "/api/auth/login", json={"username": "hossein", "password": "definitely-wrong"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password."


def test_student_login_sets_http_only_cookie_and_me(client):
    response = client.post(
        "/api/auth/login", json={"username": "hossein", "password": STUDENT_PASSWORD}
    )
    assert response.status_code == 200
    assert response.json()["role"] == "student"
    assert response.json()["userId"] == "hossein"
    assert response.json()["csrfToken"]
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie

    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["displayName"] == "Hossein"


def test_student_only_sees_own_resources(client):
    login(client, "hossein", STUDENT_PASSWORD)

    users = client.get("/api/users")
    assert users.status_code == 200
    assert [user["id"] for user in users.json()] == ["hossein"]
    assert client.get("/api/users/ali").status_code == 403

    activities = client.get("/api/activities")
    assert activities.status_code == 200
    assert all(activity["userId"] == "hossein" for activity in activities.json())

    projects = client.get("/api/projects")
    assert projects.status_code == 200
    assert all(project["userId"] == "hossein" for project in projects.json())


def test_student_activity_crud_requires_csrf_and_ownership(client):
    csrf = login(client, "hossein", STUDENT_PASSWORD)
    payload = {
        "userId": "hossein",
        "date": "2026-09-01",
        "title": "Review pull requests",
        "status": "planned",
        "projectId": "team-foundation",
    }

    assert client.post("/api/activities", json=payload).status_code == 403

    created = client.post("/api/activities", json=payload, headers={"X-CSRF-Token": csrf})
    assert created.status_code == 201
    activity_id = created.json()["id"]

    cross_user = {**payload, "userId": "ali", "projectId": None}
    assert (
        client.post("/api/activities", json=cross_user, headers={"X-CSRF-Token": csrf}).status_code
        == 403
    )

    updated = client.put(
        f"/api/activities/{activity_id}",
        json={**payload, "date": "2026-09-02", "title": "Review and merge", "status": "completed"},
        headers={"X-CSRF-Token": csrf},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "completed"

    deleted = client.delete(
        f"/api/activities/{activity_id}", headers={"X-CSRF-Token": csrf}
    )
    assert deleted.status_code == 204
    assert all(item["id"] != activity_id for item in client.get("/api/activities").json())


def test_professor_sees_team_dashboard_but_cannot_write(client):
    csrf = login(client, "professor", PROFESSOR_PASSWORD)

    users = client.get("/api/users")
    assert [user["id"] for user in users.json()] == ["ali", "hossein", "reza"]

    dashboard = client.get("/api/professor/dashboard")
    assert dashboard.status_code == 200
    body = dashboard.json()
    assert body["totals"]["members"] == 3
    assert {member["user"]["id"] for member in body["members"]} == {"ali", "hossein", "reza"}
    assert isinstance(body["recentActivities"], list)

    blocked = client.post(
        "/api/activities",
        json={
            "userId": "hossein",
            "date": "2026-09-01",
            "title": "Professor should not edit",
            "status": "planned",
            "projectId": None,
        },
        headers={"X-CSRF-Token": csrf},
    )
    assert blocked.status_code == 403


def test_student_cannot_open_professor_dashboard(client):
    login(client, "hossein", STUDENT_PASSWORD)
    assert client.get("/api/professor/dashboard").status_code == 403


def test_logout_revokes_session(client):
    csrf = login(client, "hossein", STUDENT_PASSWORD)
    assert client.get("/api/auth/me").status_code == 200
    assert client.post("/api/auth/logout", headers={"X-CSRF-Token": csrf}).status_code == 204
    assert client.get("/api/auth/me").status_code == 401


def test_professor_unknown_user_returns_structured_404(client):
    login(client, "professor", PROFESSOR_PASSWORD)
    response = client.get("/api/users/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"] == "Not Found"
