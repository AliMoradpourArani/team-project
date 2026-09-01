from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.auth_dependencies import get_current_principal
from backend.app.main import app
from backend.schemas.api import ProjectResponse
from backend.schemas.project_runner import ProjectRunResponse
from backend.services import project_runner
from backend.services.auth import Principal


def project() -> ProjectResponse:
    return ProjectResponse(
        id="demo-project",
        userId="hossein",
        name="Demo Project",
        description="Runner test project",
        technology=["python"],
        status="active",
    )


def write_project(tmp_path: Path, **overrides) -> Path:
    directory = tmp_path / "projects" / "hossein" / "demo"
    directory.mkdir(parents=True)
    manifest = {
        "id": "demo-project",
        "name": "Demo Project",
        "owner_id": "hossein",
        "description": "Runner test project",
        "technology": ["python"],
        "project_type": "cli",
        "runner": "python-script-v1",
        "entry_point": "main.py",
        "repository_path": "projects/hossein/demo",
    }
    manifest.update(overrides)
    (directory / "project.json").write_text(json.dumps(manifest), encoding="utf-8")
    (directory / "main.py").write_text('print("runner-ok")\n', encoding="utf-8")
    return tmp_path / "projects"


def test_ready_project_is_visible_but_not_runnable_by_default(tmp_path, monkeypatch):
    root = write_project(tmp_path)
    monkeypatch.setenv("PROJECTS_ROOT", str(root))
    monkeypatch.delenv("PROJECT_RUNNER_ENABLED", raising=False)

    integration = project_runner.list_integrations([project()])[0]

    assert integration.integrationStatus == "ready"
    assert integration.runner == "python-script-v1"
    assert integration.runnerEnabled is False
    assert integration.runnable is False
    assert "disabled" in (integration.reason or "").lower()


def test_allowlisted_python_project_runs_without_shell(tmp_path, monkeypatch):
    root = write_project(tmp_path)
    monkeypatch.setenv("PROJECTS_ROOT", str(root))
    monkeypatch.setenv("PROJECT_RUNNER_ENABLED", "true")
    monkeypatch.setenv("PROJECT_RUNNER_TIMEOUT_SECONDS", "2")

    result = project_runner.run_project(project())

    assert result.exitCode == 0
    assert result.timedOut is False
    assert result.stdout == "runner-ok\n"
    assert result.stderr == ""
    assert result.runner == "python-script-v1"


def test_free_form_run_field_is_rejected(tmp_path, monkeypatch):
    root = write_project(tmp_path, run="python main.py && touch /tmp/nope")
    monkeypatch.setenv("PROJECTS_ROOT", str(root))
    monkeypatch.setenv("PROJECT_RUNNER_ENABLED", "true")

    integration = project_runner.list_integrations([project()])[0]

    assert integration.integrationStatus == "invalid"
    assert integration.runnable is False


def test_path_traversal_entry_point_is_rejected(tmp_path, monkeypatch):
    root = write_project(tmp_path, entry_point="../main.py")
    monkeypatch.setenv("PROJECTS_ROOT", str(root))
    monkeypatch.setenv("PROJECT_RUNNER_ENABLED", "true")

    integration = project_runner.list_integrations([project()])[0]

    assert integration.integrationStatus == "invalid"
    assert integration.runnable is False


def test_authoritative_owner_must_match_manifest(tmp_path, monkeypatch):
    root = write_project(tmp_path, owner_id="ali")
    monkeypatch.setenv("PROJECTS_ROOT", str(root))
    monkeypatch.setenv("PROJECT_RUNNER_ENABLED", "true")

    integration = project_runner.list_integrations([project()])[0]

    assert integration.integrationStatus == "invalid"
    assert "owner" in (integration.reason or "").lower()


def test_disabled_runner_raises_before_execution(tmp_path, monkeypatch):
    root = write_project(tmp_path)
    monkeypatch.setenv("PROJECTS_ROOT", str(root))
    monkeypatch.setenv("PROJECT_RUNNER_ENABLED", "false")

    with pytest.raises(project_runner.ProjectRunnerDisabled):
        project_runner.run_project(project())


def test_project_run_api_is_csrf_protected_and_maps_disabled_runner(monkeypatch):
    from backend.app.api import projects as projects_api

    principal = Principal(
        account_id=1,
        username="hossein",
        role="student",
        user_id="hossein",
        csrf_token="csrf-test",
    )
    app.dependency_overrides[get_current_principal] = lambda: principal
    monkeypatch.setattr(projects_api.queries, "list_projects", lambda: [project()])
    monkeypatch.setattr(
        projects_api.project_runner,
        "run_project",
        lambda _project: (_ for _ in ()).throw(project_runner.ProjectRunnerDisabled("disabled")),
    )

    try:
        client = TestClient(app)
        missing_csrf = client.post("/api/projects/demo-project/run")
        assert missing_csrf.status_code == 403

        disabled = client.post(
            "/api/projects/demo-project/run", headers={"X-CSRF-Token": "csrf-test"}
        )
        assert disabled.status_code == 503
        assert disabled.json()["detail"] == "disabled"
    finally:
        app.dependency_overrides.clear()


def test_student_cannot_run_another_users_project(monkeypatch):
    from backend.app.api import projects as projects_api

    principal = Principal(
        account_id=1,
        username="hossein",
        role="student",
        user_id="hossein",
        csrf_token="csrf-test",
    )
    other = ProjectResponse(
        id="ali-project",
        userId="ali",
        name="Ali Project",
        description="Other user's project",
        technology=["python"],
        status="active",
    )
    app.dependency_overrides[get_current_principal] = lambda: principal
    monkeypatch.setattr(projects_api.queries, "list_projects", lambda: [project(), other])
    monkeypatch.setattr(
        projects_api.project_runner,
        "run_project",
        lambda _project: ProjectRunResponse(
            projectId="ali-project",
            runner="python-script-v1",
            exitCode=0,
            timedOut=False,
            durationMs=1,
            stdout="",
            stderr="",
            outputTruncated=False,
        ),
    )

    try:
        client = TestClient(app)
        response = client.post(
            "/api/projects/ali-project/run", headers={"X-CSRF-Token": "csrf-test"}
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
