"""API tests against the FastAPI application with an isolated database."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.database.init_db import initialize_database


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """Provide a TestClient over a fresh, seeded database in a temp directory."""
    database_path = tmp_path / "test.db"
    initialize_database(database_path, seed=True)
    monkeypatch.setenv("DATABASE_PATH", str(database_path))
    with TestClient(app) as test_client:
        yield test_client


def test_api_health_returns_ok(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_legacy_health_endpoint_still_works(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_get_users_returns_example_team_members(client):
    response = client.get("/api/users")

    assert response.status_code == 200
    assert [user["id"] for user in response.json()] == ["ali", "hossein", "reza"]


@pytest.mark.parametrize("user_id", ["hossein", "ali", "reza"])
def test_get_user_returns_member(client, user_id):
    response = client.get(f"/api/users/{user_id}")

    assert response.status_code == 200
    assert response.json()["id"] == user_id


def test_get_unknown_user_returns_structured_404(client):
    response = client.get("/api/users/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"] == "Not Found"


def test_get_activities_returns_tracked_activities(client):
    response = client.get("/api/activities")

    assert response.status_code == 200
    activities = response.json()
    assert activities[0]["userId"] == "ali"
    assert all(activity["id"] for activity in activities)


def test_get_projects_returns_project_collection(client):
    response = client.get("/api/projects")

    assert response.status_code == 200
    projects = response.json()
    assert {project["id"] for project in projects} >= {"team-foundation"}
    assert all(isinstance(project["technology"], list) for project in projects)
