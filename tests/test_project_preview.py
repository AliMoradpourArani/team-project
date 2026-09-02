from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.schemas.api import ProjectResponse
from backend.schemas.project_runner import ProjectManifest
from backend.services import project_runner


def project(project_id: str = "demo-project") -> ProjectResponse:
    return ProjectResponse(
        id=project_id,
        userId="hossein",
        name="Demo Project",
        description="Rich demo project",
        technology=["html"],
        status="active",
    )


def write_manifest_project(
    tmp_path: Path,
    *,
    project_type: str,
    runner: str,
    entry_point: str,
    entry_content: str,
) -> Path:
    directory = tmp_path / "projects" / "hossein" / "demo"
    directory.mkdir(parents=True)
    manifest = {
        "id": "demo-project",
        "name": "Demo Project",
        "owner_id": "hossein",
        "description": "Rich demo project",
        "technology": ["html"],
        "project_type": project_type,
        "runner": runner,
        "entry_point": entry_point,
        "repository_path": "projects/hossein/demo",
    }
    (directory / "project.json").write_text(json.dumps(manifest), encoding="utf-8")
    (directory / entry_point).write_text(entry_content, encoding="utf-8")
    (directory / "README.md").write_text("# Demo\n", encoding="utf-8")
    return tmp_path / "projects"


def test_static_site_is_ready_and_previewable_without_enabling_runner(tmp_path, monkeypatch):
    root = write_manifest_project(
        tmp_path,
        project_type="static-web",
        runner="static-site-v1",
        entry_point="index.html",
        entry_content="<h1>Static demo</h1><script>alert('blocked by sandbox')</script>",
    )
    monkeypatch.setenv("PROJECTS_ROOT", str(root))
    monkeypatch.delenv("PROJECT_RUNNER_ENABLED", raising=False)
    monkeypatch.setattr(project_runner, "list_run_history", lambda _project_id: [])

    integration = project_runner.list_integrations([project()])[0]
    detail = project_runner.project_detail(project())

    assert integration.integrationStatus == "ready"
    assert integration.demoMode == "preview"
    assert integration.previewable is True
    assert integration.runnable is False
    assert detail.preview is not None
    assert detail.preview.kind == "static-html"
    assert "Static demo" in detail.preview.content


def test_openapi_json_preview_is_validated_and_normalized(tmp_path, monkeypatch):
    spec = {
        "openapi": "3.1.0",
        "info": {"title": "Student API", "version": "1.0.0"},
        "paths": {"/health": {"get": {"responses": {"200": {"description": "ok"}}}}},
    }
    root = write_manifest_project(
        tmp_path,
        project_type="api",
        runner="openapi-json-v1",
        entry_point="openapi.json",
        entry_content=json.dumps(spec),
    )
    monkeypatch.setenv("PROJECTS_ROOT", str(root))
    monkeypatch.setattr(project_runner, "list_run_history", lambda _project_id: [])

    detail = project_runner.project_detail(project())

    assert detail.integration.integrationStatus == "ready"
    assert detail.integration.previewable is True
    assert detail.preview is not None
    assert detail.preview.kind == "openapi-json"
    assert "Student API" in detail.preview.summary
    assert '"/health"' in detail.preview.content


def test_invalid_openapi_document_makes_integration_invalid(tmp_path, monkeypatch):
    root = write_manifest_project(
        tmp_path,
        project_type="api",
        runner="openapi-json-v1",
        entry_point="openapi.json",
        entry_content=json.dumps({"openapi": "2.0", "paths": {}}),
    )
    monkeypatch.setenv("PROJECTS_ROOT", str(root))

    integration = project_runner.list_integrations([project()])[0]

    assert integration.integrationStatus == "invalid"
    assert integration.previewable is False
    assert "OpenAPI 3.x" in (integration.reason or "")


def test_preview_only_project_cannot_use_process_runner(tmp_path, monkeypatch):
    root = write_manifest_project(
        tmp_path,
        project_type="static-web",
        runner="static-site-v1",
        entry_point="index.html",
        entry_content="<h1>Preview only</h1>",
    )
    monkeypatch.setenv("PROJECTS_ROOT", str(root))
    monkeypatch.setenv("PROJECT_RUNNER_ENABLED", "true")

    with pytest.raises(project_runner.ProjectManifestError, match="preview-only"):
        project_runner.run_project(project())


def test_manifest_rejects_mismatched_project_type_and_runner():
    with pytest.raises(ValueError):
        ProjectManifest.model_validate(
            {
                "id": "demo-project",
                "name": "Demo",
                "owner_id": "hossein",
                "description": "Invalid pair",
                "technology": [],
                "project_type": "api",
                "runner": "python-script-v1",
                "entry_point": "main.py",
                "repository_path": "projects/hossein/demo",
            }
        )
