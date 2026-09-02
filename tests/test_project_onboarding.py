from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.auth_dependencies import get_current_principal
from backend.app.main import app
from backend.database.init_db import initialize_database
from backend.schemas.api import ProjectResponse
from backend.services import project_onboarding
from backend.services.auth import Principal


def project(project_id: str = "demo-project", user_id: str = "hossein") -> ProjectResponse:
    return ProjectResponse(
        id=project_id,
        userId=user_id,
        name="Demo Project",
        description="Onboarding test project",
        technology=["python"],
        status="active",
    )


def write_project(tmp_path: Path, *, include_readme: bool = True, **overrides) -> Path:
    directory = tmp_path / "projects" / "hossein" / "demo"
    directory.mkdir(parents=True)
    manifest = {
        "id": "demo-project",
        "name": "Demo Project",
        "owner_id": "hossein",
        "description": "Onboarding test project",
        "technology": ["python"],
        "project_type": "cli",
        "runner": "python-script-v1",
        "entry_point": "main.py",
        "repository_path": "projects/hossein/demo",
    }
    manifest.update(overrides)
    (directory / "project.json").write_text(json.dumps(manifest), encoding="utf-8")
    (directory / "main.py").write_text('print("ready")\n', encoding="utf-8")
    if include_readme:
        (directory / "README.md").write_text(
            "# Demo\n\nPurpose, setup, input, output, and demo instructions.\n",
            encoding="utf-8",
        )
    return tmp_path / "projects"


def prepare_runtime(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "runtime.db"
    monkeypatch.setenv("DATABASE_PATH", str(database_path))
    initialize_database(database_path)


def test_ready_project_completes_shared_onboarding_gates(tmp_path, monkeypatch):
    prepare_runtime(tmp_path, monkeypatch)
    monkeypatch.setenv("PROJECTS_ROOT", str(write_project(tmp_path)))

    onboarding = project_onboarding.get_onboarding(project())

    assert onboarding.status == "ready"
    assert onboarding.readyForSubmission is True
    assert onboarding.completedGates == onboarding.totalGates == 6
    assert onboarding.expectedMetadataPath == "data/projects/demo-project.json"
    assert onboarding.expectedRepositoryPath == "projects/hossein/demo"
    assert onboarding.localCheckCommand == "make project-check PROJECT_ID=demo-project"
    assert {item.runner for item in onboarding.supportedContracts} == {
        "python-script-v1",
        "static-site-v1",
        "openapi-json-v1",
    }


def test_missing_readme_is_pending_with_actionable_remediation(tmp_path, monkeypatch):
    prepare_runtime(tmp_path, monkeypatch)
    monkeypatch.setenv(
        "PROJECTS_ROOT", str(write_project(tmp_path, include_readme=False))
    )

    onboarding = project_onboarding.get_onboarding(project())

    assert onboarding.status == "pending"
    assert onboarding.readyForSubmission is False
    readme = next(gate for gate in onboarding.gates if gate.key == "readme")
    assert readme.passed is False
    assert "README.md" in readme.remediation
    assert onboarding.nextAction == readme.remediation


def test_invalid_manifest_is_distinct_from_not_yet_integrated(tmp_path, monkeypatch):
    prepare_runtime(tmp_path, monkeypatch)
    monkeypatch.setenv(
        "PROJECTS_ROOT",
        str(write_project(tmp_path, run="python main.py && touch /tmp/nope")),
    )

    onboarding = project_onboarding.get_onboarding(project())

    assert onboarding.status == "invalid"
    assert onboarding.readyForSubmission is False
    manifest = next(gate for gate in onboarding.gates if gate.key == "manifest")
    assert manifest.passed is False


def test_student_onboarding_api_preserves_project_ownership(tmp_path, monkeypatch):
    from backend.app.api import projects as projects_api

    prepare_runtime(tmp_path, monkeypatch)
    monkeypatch.setenv("PROJECTS_ROOT", str(write_project(tmp_path)))
    principal = Principal(
        account_id=1,
        username="hossein",
        role="student",
        user_id="hossein",
        csrf_token="csrf-test",
    )
    other = project(project_id="ali-project", user_id="ali")
    app.dependency_overrides[get_current_principal] = lambda: principal
    monkeypatch.setattr(projects_api.queries, "list_projects", lambda: [project(), other])

    try:
        client = TestClient(app)
        own = client.get("/api/projects/demo-project/onboarding")
        assert own.status_code == 200
        assert own.json()["status"] == "ready"

        hidden = client.get("/api/projects/ali-project/onboarding")
        assert hidden.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_submission_status_is_blocked_until_onboarding_is_ready(tmp_path, monkeypatch):
    from backend.app.api import projects as projects_api

    prepare_runtime(tmp_path, monkeypatch)
    empty_projects_root = tmp_path / "projects"
    empty_projects_root.mkdir()
    monkeypatch.setenv("PROJECTS_ROOT", str(empty_projects_root))
    principal = Principal(
        account_id=1,
        username="hossein",
        role="student",
        user_id="hossein",
        csrf_token="csrf-test",
    )
    app.dependency_overrides[get_current_principal] = lambda: principal
    monkeypatch.setattr(projects_api.queries, "list_projects", lambda: [project()])

    try:
        response = TestClient(app).get("/api/projects/demo-project/submission")
        assert response.status_code == 200
        body = response.json()
        assert body["canSubmit"] is False
        assert "onboarding gates" in body["blockedReason"].lower()
    finally:
        app.dependency_overrides.clear()
