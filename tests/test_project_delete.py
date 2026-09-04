"""Imported-project deletion (no real filesystem)."""

from __future__ import annotations

import json
import shutil

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.database import source_files
from backend.database.connection import REPOSITORY_ROOT
from backend.database.init_db import initialize_database
from backend.schemas.api import ProjectResponse
from backend.services import code_editor
from backend.services.auth import create_or_update_account

STUDENT_PASSWORD = "student-pass-123"


@pytest.fixture()
def client(tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    shutil.copytree(REPOSITORY_ROOT / "data", data_root)
    monkeypatch.setattr(source_files, "DATA_ROOT", data_root)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    projects_root = tmp_path / "projects"
    monkeypatch.setenv("PROJECTS_ROOT", str(projects_root))
    # Seed a minimal ali/hello project both on disk and in source data
    projects_root.mkdir(parents=True, exist_ok=True)
    directory = projects_root / "ali" / "hello"
    directory.mkdir(parents=True)
    (directory / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (directory / "project.json").write_text(
        json.dumps(
            {
                "id": "hello",
                "name": "hello",
                "owner_id": "ali",
                "description": "demo",
                "technology": ["Python"],
                "project_type": "cli",
                "runner": "python-script-v1",
                "entry_point": "main.py",
                "repository_path": "projects/ali/hello",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (data_root / "projects" / "hello.json").write_text(
        json.dumps(
            {
                "id": "hello",
                "owner_id": "ali",
                "name": "hello",
                "description": "demo",
                "technology": ["Python"],
                "status": "active",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    initialize_database(tmp_path / "test.db", seed=True)
    create_or_update_account(
        username="ali", password=STUDENT_PASSWORD, role="student", user_id="ali"
    )
    create_or_update_account(
        username="professor", password="prof-pass-123", role="professor", user_id=None
    )
    create_or_update_account(
        username="reza", password=STUDENT_PASSWORD, role="student", user_id="reza"
    )
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, username="ali", password=STUDENT_PASSWORD) -> str:
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["csrfToken"]


def test_delete_project_service_removes_source_and_directory(tmp_path, monkeypatch):
    data_root = tmp_path / "data"
    shutil.copytree(REPOSITORY_ROOT / "data", data_root)
    monkeypatch.setattr(source_files, "DATA_ROOT", data_root)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    projects_root = tmp_path / "projects"
    monkeypatch.setenv("PROJECTS_ROOT", str(projects_root))
    initialize_database(tmp_path / "test.db", seed=True)

    # Add an extra project on top of the seeded data (so FK users exist)
    projects_root.mkdir(parents=True, exist_ok=True)
    directory = projects_root / "ali" / "hello"
    directory.mkdir(parents=True)
    (directory / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (directory / "project.json").write_text(
        json.dumps(
            {
                "id": "hello",
                "name": "hello",
                "owner_id": "ali",
                "description": "demo",
                "technology": ["Python"],
                "project_type": "cli",
                "runner": "python-script-v1",
                "entry_point": "main.py",
                "repository_path": "projects/ali/hello",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (data_root / "projects" / "hello.json").write_text(
        json.dumps(
            {
                "id": "hello",
                "owner_id": "ali",
                "name": "hello",
                "description": "demo",
                "technology": ["Python"],
                "status": "active",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    from backend.database.connection import connect
    from backend.database.sync_data import sync_source_data

    with connect(tmp_path / "test.db") as connection:
        sync_source_data(connection)

    project = ProjectResponse(
        id="hello",
        userId="ali",
        name="hello",
        description="demo",
        technology=["Python"],
        status="active",
    )
    code_editor.delete_project(project)

    assert directory.exists() is False
    assert (data_root / "projects" / "hello.json").exists() is False

    from backend.services.queries import list_projects

    assert all(candidate.id != "hello" for candidate in list_projects())


def test_delete_endpoint_owner_only_and_csrf(client):
    csrf = login(client, "ali")
    # Missing CSRF -> 403
    response = client.delete("/api/projects/hello")
    assert response.status_code == 403

    # Other student cannot see ali's project at all (404, not 403) — ownership is enforced
    other_csrf = login(client, "reza")
    response = client.delete("/api/projects/hello", headers={"X-CSRF-Token": other_csrf})
    assert response.status_code == 404

    # Anonymous -> 401
    anon = TestClient(app)
    with anon:
        response = anon.delete("/api/projects/hello", headers={"X-CSRF-Token": csrf})
        assert response.status_code == 401


def test_delete_endpoint_removes_project(client):
    csrf = login(client, "ali")
    ids_before = {candidate["id"] for candidate in client.get("/api/projects").json()}
    assert "hello" in ids_before

    response = client.delete("/api/projects/hello", headers={"X-CSRF-Token": csrf})
    assert response.status_code == 204

    ids_after = {candidate["id"] for candidate in client.get("/api/projects").json()}
    assert "hello" not in ids_after
    assert client.get("/api/projects/hello/files").status_code == 404


def test_delete_project_rollback_when_sync_fails(tmp_path, monkeypatch):
    """If DB resync fails, filesystem/source-of-truth must be fully restored."""

    data_root = tmp_path / "data"
    shutil.copytree(REPOSITORY_ROOT / "data", data_root)
    monkeypatch.setattr(source_files, "DATA_ROOT", data_root)
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    projects_root = tmp_path / "projects"
    monkeypatch.setenv("PROJECTS_ROOT", str(projects_root))
    initialize_database(tmp_path / "test.db", seed=True)

    projects_root.mkdir(parents=True, exist_ok=True)
    directory = projects_root / "ali" / "hello"
    directory.mkdir(parents=True)
    (directory / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (directory / "project.json").write_text(
        json.dumps(
            {
                "id": "hello",
                "name": "hello",
                "owner_id": "ali",
                "description": "demo",
                "technology": ["Python"],
                "project_type": "cli",
                "runner": "python-script-v1",
                "entry_point": "main.py",
                "repository_path": "projects/ali/hello",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    record_path = data_root / "projects" / "hello.json"
    record_path.write_text(
        json.dumps(
            {
                "id": "hello",
                "owner_id": "ali",
                "name": "hello",
                "description": "demo",
                "technology": ["Python"],
                "status": "active",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    from backend.database.connection import connect
    from backend.database.sync_data import sync_source_data

    with connect(tmp_path / "test.db") as connection:
        sync_source_data(connection)

    original_bytes = record_path.read_bytes()
    assert directory.exists()

    # Force the DB sync step to fail after filesystem changes
    monkeypatch.setattr(
        "backend.database.sync_data.sync_source_data",
        lambda _conn: (_ for _ in ()).throw(RuntimeError("sync boom")),
    )

    project = ProjectResponse(
        id="hello",
        userId="ali",
        name="hello",
        description="demo",
        technology=["Python"],
        status="active",
    )
    with pytest.raises(RuntimeError, match="sync boom"):
        code_editor.delete_project(project)

    # Nothing was partially deleted
    assert record_path.exists()
    assert record_path.read_bytes() == original_bytes
    assert directory.exists()
    assert (directory / "main.py").exists()

    from backend.services.queries import list_projects

    assert any(candidate.id == "hello" for candidate in list_projects())
