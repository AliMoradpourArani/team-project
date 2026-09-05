from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.auth_dependencies import get_current_principal
from backend.app.main import app
from backend.database.connection import connect
from backend.database.init_db import initialize_database
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
    (directory / "README.md").write_text("# Demo Project\n\nIntegration test project.\n", encoding="utf-8")
    return tmp_path / "projects"


def test_ready_project_is_runnable_by_default(tmp_path, monkeypatch):
    root = write_project(tmp_path)
    monkeypatch.setenv("PROJECTS_ROOT", str(root))
    monkeypatch.delenv("PROJECT_RUNNER_ENABLED", raising=False)

    integration = project_runner.list_integrations([project()])[0]

    assert integration.integrationStatus == "ready"
    assert integration.runner == "python-script-v1"
    assert integration.runnerEnabled is True
    assert integration.runnable is True
    assert integration.reason is None


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


def test_project_detail_reports_health_and_readme(tmp_path, monkeypatch):
    root = write_project(tmp_path)
    monkeypatch.setenv("PROJECTS_ROOT", str(root))
    monkeypatch.setattr(project_runner, "list_run_history", lambda _project_id: [])

    detail = project_runner.project_detail(project())

    assert detail.integration.integrationStatus == "ready"
    assert detail.healthPassed == detail.healthTotal == 6
    assert detail.readme is not None
    assert "Demo Project" in detail.readme
    assert all(check.passed for check in detail.health)


def test_missing_readme_is_visible_as_health_failure(tmp_path, monkeypatch):
    root = write_project(tmp_path)
    (root / "hossein" / "demo" / "README.md").unlink()
    monkeypatch.setenv("PROJECTS_ROOT", str(root))
    monkeypatch.setattr(project_runner, "list_run_history", lambda _project_id: [])

    detail = project_runner.project_detail(project())

    assert detail.integration.integrationStatus == "ready"
    readme_check = next(check for check in detail.health if check.key == "readme")
    assert readme_check.passed is False
    assert detail.healthPassed == 5
    assert detail.readme is None


def test_run_history_is_runtime_only_and_bounded(tmp_path, monkeypatch):
    database_path = tmp_path / "runtime.db"
    initialize_database(database_path)
    monkeypatch.setenv("DATABASE_PATH", str(database_path))

    with connect(database_path) as connection:
        connection.execute("INSERT INTO users (id, display_name, role) VALUES (?, ?, ?)", ("hossein", "Hossein", "Developer"))
        connection.execute(
            "INSERT INTO projects (id, user_id, name, description, technology, status) VALUES (?, ?, ?, ?, ?, ?)",
            ("demo-project", "hossein", "Demo Project", "Runner test project", "python", "active"),
        )
        connection.commit()

    result = ProjectRunResponse(
        projectId="demo-project",
        runner="python-script-v1",
        exitCode=0,
        timedOut=False,
        durationMs=12,
        stdout="x" * 5000,
        stderr="",
        outputTruncated=False,
    )
    project_runner.record_run(result)

    history = project_runner.list_run_history("demo-project")

    assert len(history) == 1
    assert history[0].exitCode == 0
    assert history[0].durationMs == 12
    assert history[0].outputTruncated is True
    assert "output truncated" in history[0].stdoutPreview


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


def test_project_detail_api_preserves_student_visibility(monkeypatch):
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

    try:
        client = TestClient(app)
        response = client.get("/api/projects/ali-project/detail")
        assert response.status_code == 404
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
