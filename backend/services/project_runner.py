"""Controlled local execution and rich integration details for reviewed student projects."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from pydantic import ValidationError

from ..database.connection import REPOSITORY_ROOT, connect
from ..schemas.api import ProjectResponse
from ..schemas.project_runner import (
    ProjectDetailResponse,
    ProjectHealthCheck,
    ProjectIntegrationResponse,
    ProjectManifest,
    ProjectPreview,
    ProjectRunHistoryItem,
    ProjectRunResponse,
)
from ..schemas.source_data import validate_slug

DEFAULT_TIMEOUT_SECONDS = 5
MAX_TIMEOUT_SECONDS = 30
DEFAULT_OUTPUT_LIMIT = 16_000
README_DISPLAY_LIMIT = 64_000
PREVIEW_SOURCE_LIMIT = 1_000_000
PREVIEW_DISPLAY_LIMIT = 100_000
RUN_HISTORY_LIMIT = 10
RUN_PREVIEW_LIMIT = 4_000


class ProjectRunnerError(RuntimeError):
    """Base error for manifest discovery and controlled execution."""


class ProjectRunnerDisabled(ProjectRunnerError):
    """Raised when execution is disabled by runtime configuration."""


class ProjectManifestError(ProjectRunnerError):
    """Raised when a project manifest or path violates the demo contract."""


def runner_enabled() -> bool:
    # Execution is enabled by default for local development so the code-editor
    # "Run" works out of the box. Set PROJECT_RUNNER_ENABLED=false to disable
    # process execution (an explicit kill switch for locked-down deployments).
    return os.getenv("PROJECT_RUNNER_ENABLED", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _projects_root() -> Path:
    configured = os.getenv("PROJECTS_ROOT")
    return Path(configured).resolve() if configured else (REPOSITORY_ROOT / "projects").resolve()


def _timeout_seconds() -> int:
    raw = os.getenv("PROJECT_RUNNER_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
    try:
        value = int(raw)
    except ValueError as error:
        raise ProjectRunnerError("PROJECT_RUNNER_TIMEOUT_SECONDS must be an integer.") from error
    return max(1, min(value, MAX_TIMEOUT_SECONDS))


def _output_limit() -> int:
    raw = os.getenv("PROJECT_RUNNER_OUTPUT_LIMIT", str(DEFAULT_OUTPUT_LIMIT))
    try:
        value = int(raw)
    except ValueError as error:
        raise ProjectRunnerError("PROJECT_RUNNER_OUTPUT_LIMIT must be an integer.") from error
    return max(1_000, min(value, 100_000))


def _read_manifest(path: Path) -> ProjectManifest:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ProjectManifestError(f"Cannot read project manifest {path}: {error}") from error
    try:
        return ProjectManifest.model_validate(payload)
    except ValidationError as error:
        raise ProjectManifestError(
            f"Invalid project manifest {path}: {error.errors()[:3]}"
        ) from error


def _raw_manifest_id(path: Path) -> str | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = payload.get("id") if isinstance(payload, dict) else None
    if not isinstance(value, str):
        return None
    try:
        return validate_slug(value, "project manifest id")
    except ValueError:
        return None


def _manifest_index() -> tuple[dict[str, tuple[ProjectManifest, Path]], dict[str, str]]:
    manifests: dict[str, tuple[ProjectManifest, Path]] = {}
    errors: dict[str, str] = {}
    root = _projects_root()
    if not root.is_dir():
        return manifests, errors

    for path in sorted(root.glob("*/*/project.json")):
        raw_id = _raw_manifest_id(path)
        try:
            manifest = _read_manifest(path)
        except ProjectManifestError as error:
            if raw_id is not None:
                errors[raw_id] = str(error)
            continue
        if manifest.id in manifests:
            errors[manifest.id] = f"Duplicate project manifest id {manifest.id!r}."
            manifests.pop(manifest.id, None)
            continue
        if manifest.id in errors:
            continue
        manifests[manifest.id] = (manifest, path)
    return manifests, errors


def _resolve_project_paths(manifest: ProjectManifest, manifest_path: Path) -> tuple[Path, Path]:
    root = _projects_root()
    repository_root = root.parent
    declared_dir = (repository_root / manifest.repository_path).resolve()
    actual_dir = manifest_path.parent.resolve()

    if actual_dir != declared_dir:
        raise ProjectManifestError("Manifest repository_path does not match its actual directory.")
    if root not in actual_dir.parents:
        raise ProjectManifestError("Project directory escaped the configured projects root.")
    if manifest_path.parent.is_symlink():
        raise ProjectManifestError("Symlinked project directories are not supported.")

    relative = Path(manifest.entry_point)
    entry_point = (actual_dir / relative).resolve()
    if actual_dir not in entry_point.parents:
        raise ProjectManifestError("Project entry point escaped its project directory.")
    if not entry_point.is_file():
        raise ProjectManifestError(f"Project entry point does not exist: {manifest.entry_point}")

    cursor = actual_dir
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise ProjectManifestError("Symlinked entry-point paths are not supported.")

    owner_dir = Path(manifest.repository_path).parts[1]
    if owner_dir != manifest.owner_id:
        raise ProjectManifestError("Manifest owner_id must match its projects/<owner>/ directory.")
    return actual_dir, entry_point


def _demo_mode(manifest: ProjectManifest) -> str:
    return "execute" if manifest.runner == "python-script-v1" else "preview"


def _bounded_text(path: Path, label: str) -> tuple[str, bool]:
    try:
        size = path.stat().st_size
    except OSError as error:
        raise ProjectManifestError(f"Cannot inspect {label}: {error}") from error
    if size > PREVIEW_SOURCE_LIMIT:
        raise ProjectManifestError(
            f"{label} is too large for an in-app preview ({size} bytes; limit {PREVIEW_SOURCE_LIMIT})."
        )
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ProjectManifestError(f"Cannot read {label} as UTF-8: {error}") from error
    if len(text) <= PREVIEW_DISPLAY_LIMIT:
        return text, False
    return text[:PREVIEW_DISPLAY_LIMIT] + "\n[preview truncated]", True


def _project_preview(manifest: ProjectManifest, entry_point: Path) -> ProjectPreview | None:
    if manifest.runner == "python-script-v1":
        return None

    if manifest.runner == "static-site-v1":
        content, truncated = _bounded_text(entry_point, "static HTML entry point")
        return ProjectPreview(
            kind="static-html",
            content=content,
            summary="Sandboxed static HTML preview. Scripts, forms, network requests, and navigation are blocked by the UI preview policy.",
            truncated=truncated,
        )

    if manifest.runner == "openapi-json-v1":
        raw, source_truncated = _bounded_text(entry_point, "OpenAPI JSON entry point")
        if source_truncated:
            raise ProjectManifestError("OpenAPI JSON must fit within the preview display limit.")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as error:
            raise ProjectManifestError(f"OpenAPI entry point is not valid JSON: {error}") from error
        if not isinstance(payload, dict):
            raise ProjectManifestError("OpenAPI entry point must contain a JSON object.")
        openapi_version = payload.get("openapi")
        paths = payload.get("paths")
        info = payload.get("info")
        if not isinstance(openapi_version, str) or not openapi_version.startswith("3."):
            raise ProjectManifestError("OpenAPI preview requires an OpenAPI 3.x document.")
        if not isinstance(paths, dict):
            raise ProjectManifestError("OpenAPI preview requires a top-level paths object.")
        if info is not None and not isinstance(info, dict):
            raise ProjectManifestError("OpenAPI info must be a JSON object when provided.")

        normalized = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        if len(normalized) > PREVIEW_DISPLAY_LIMIT:
            raise ProjectManifestError("Normalized OpenAPI JSON exceeds the in-app preview limit.")
        title = info.get("title") if isinstance(info, dict) else None
        version = info.get("version") if isinstance(info, dict) else None
        identity = " · ".join(value for value in (title, version) if isinstance(value, str) and value)
        summary = f"OpenAPI {openapi_version} · {len(paths)} paths"
        if identity:
            summary = f"{identity} · {summary}"
        return ProjectPreview(
            kind="openapi-json",
            content=normalized,
            summary=summary,
            truncated=False,
        )

    raise ProjectManifestError(f"Unsupported project runner: {manifest.runner}")


def _integration_for(
    project: ProjectResponse,
    manifests: dict[str, tuple[ProjectManifest, Path]],
    errors: dict[str, str],
) -> ProjectIntegrationResponse:
    enabled = runner_enabled()
    invalid_reason = errors.get(project.id)
    if invalid_reason:
        return ProjectIntegrationResponse(
            projectId=project.id,
            userId=project.userId,
            name=project.name,
            integrationStatus="invalid",
            runnerEnabled=enabled,
            runnable=False,
            previewable=False,
            reason=invalid_reason,
        )

    item = manifests.get(project.id)
    if item is None:
        return ProjectIntegrationResponse(
            projectId=project.id,
            userId=project.userId,
            name=project.name,
            integrationStatus="not-integrated",
            runnerEnabled=enabled,
            runnable=False,
            previewable=False,
            reason="No valid projects/<owner>/<project>/project.json manifest is linked to this project.",
        )

    manifest, manifest_path = item
    demo_mode = _demo_mode(manifest)
    try:
        if manifest.owner_id != project.userId:
            raise ProjectManifestError("Manifest owner_id does not match authoritative project owner.")
        _project_dir, entry_point = _resolve_project_paths(manifest, manifest_path)
        _project_preview(manifest, entry_point)
    except ProjectManifestError as error:
        return ProjectIntegrationResponse(
            projectId=project.id,
            userId=project.userId,
            name=project.name,
            integrationStatus="invalid",
            runnerEnabled=enabled,
            runnable=False,
            previewable=False,
            demoMode=demo_mode,
            projectType=manifest.project_type,
            runner=manifest.runner,
            entryPoint=manifest.entry_point,
            repositoryPath=manifest.repository_path,
            reason=str(error),
        )

    executable = demo_mode == "execute"
    return ProjectIntegrationResponse(
        projectId=project.id,
        userId=project.userId,
        name=project.name,
        integrationStatus="ready",
        runnerEnabled=enabled,
        runnable=enabled and executable,
        previewable=not executable,
        demoMode=demo_mode,
        projectType=manifest.project_type,
        runner=manifest.runner,
        entryPoint=manifest.entry_point,
        repositoryPath=manifest.repository_path,
        reason=(
            None
            if not executable or enabled
            else "Runner is disabled. Set PROJECT_RUNNER_ENABLED=true after reviewing project code."
        ),
    )


def list_integrations(projects: list[ProjectResponse]) -> list[ProjectIntegrationResponse]:
    manifests, errors = _manifest_index()
    return [_integration_for(project, manifests, errors) for project in projects]


def _health_check(key: str, label: str, passed: bool, detail: str) -> ProjectHealthCheck:
    return ProjectHealthCheck(key=key, label=label, passed=passed, detail=detail)


def _read_project_readme(project_dir: Path) -> tuple[str | None, ProjectHealthCheck]:
    readme_path = project_dir / "README.md"
    if not readme_path.exists():
        return None, _health_check(
            "readme",
            "README",
            False,
            "README.md is required so reviewers can understand and run the member project.",
        )
    if readme_path.is_symlink() or not readme_path.is_file():
        return None, _health_check(
            "readme", "README", False, "README.md must be a regular non-symlink file."
        )
    try:
        text = readme_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        return None, _health_check("readme", "README", False, f"README.md cannot be read: {error}")

    if len(text) > README_DISPLAY_LIMIT:
        text = text[:README_DISPLAY_LIMIT] + "\n\n[README truncated for display]"
        detail = f"README.md is present; display is limited to {README_DISPLAY_LIMIT} characters."
    else:
        detail = "README.md is present and readable."
    return text, _health_check("readme", "README", True, detail)


def project_detail(project: ProjectResponse) -> ProjectDetailResponse:
    manifests, errors = _manifest_index()
    integration = _integration_for(project, manifests, errors)
    checks = [
        _health_check(
            "project-record",
            "Tracked project metadata",
            True,
            "Project exists in authoritative data/projects metadata.",
        )
    ]
    readme: str | None = None
    preview: ProjectPreview | None = None

    invalid_reason = errors.get(project.id)
    item = manifests.get(project.id)
    if invalid_reason:
        checks.extend(
            [
                _health_check("manifest", "Manifest", False, invalid_reason),
                _health_check("owner", "Owner mapping", False, "Cannot verify owner until manifest is valid."),
                _health_check("paths", "Repository paths", False, "Cannot verify paths until manifest is valid."),
                _health_check("runner", "Demo contract", False, "Cannot verify demo contract until manifest is valid."),
                _health_check("readme", "README", False, "Cannot locate README until manifest is valid."),
            ]
        )
    elif item is None:
        checks.extend(
            [
                _health_check(
                    "manifest",
                    "Manifest",
                    False,
                    "Add projects/<owner>/<project>/project.json using the shared integration contract.",
                ),
                _health_check("owner", "Owner mapping", False, "No manifest is available to verify ownership."),
                _health_check("paths", "Repository paths", False, "No manifest is available to verify paths."),
                _health_check("runner", "Demo contract", False, "No manifest is available to verify the demo type."),
                _health_check("readme", "README", False, "No integrated project directory is available."),
            ]
        )
    else:
        manifest, manifest_path = item
        owner_ok = manifest.owner_id == project.userId
        checks.append(
            _health_check(
                "manifest",
                "Manifest",
                True,
                "project.json matches a supported typed demo contract and contains no free-form shell command.",
            )
        )
        checks.append(
            _health_check(
                "owner",
                "Owner mapping",
                owner_ok,
                "Manifest owner matches authoritative project owner."
                if owner_ok
                else "Manifest owner_id does not match authoritative project owner.",
            )
        )
        try:
            project_dir, entry_point = _resolve_project_paths(manifest, manifest_path)
        except ProjectManifestError as error:
            checks.append(_health_check("paths", "Repository paths", False, str(error)))
            checks.append(
                _health_check(
                    "runner",
                    "Demo contract",
                    False,
                    "Demo cannot be considered ready until repository paths are valid.",
                )
            )
            checks.append(
                _health_check("readme", "README", False, "README cannot be loaded from an invalid project path.")
            )
        else:
            checks.append(
                _health_check(
                    "paths",
                    "Repository paths",
                    True,
                    "Repository directory and entry point are confined to the member project.",
                )
            )
            try:
                preview = _project_preview(manifest, entry_point)
            except ProjectManifestError as error:
                checks.append(_health_check("runner", "Demo contract", False, str(error)))
            else:
                mode = "controlled execution" if _demo_mode(manifest) == "execute" else "safe preview"
                checks.append(
                    _health_check(
                        "runner",
                        "Demo contract",
                        True,
                        f"Supported contract: {manifest.project_type} / {manifest.runner} ({mode}).",
                    )
                )
            readme, readme_check = _read_project_readme(project_dir)
            checks.append(readme_check)

    history = list_run_history(project.id)
    passed = sum(check.passed for check in checks)
    return ProjectDetailResponse(
        project=project,
        integration=integration,
        health=checks,
        healthPassed=passed,
        healthTotal=len(checks),
        readme=readme,
        preview=preview,
        recentRuns=history,
    )


def _truncate(value: str, limit: int) -> tuple[str, bool]:
    if len(value) <= limit:
        return value, False
    return value[:limit] + "\n[output truncated]", True


def _timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value


def list_run_history(project_id: str, limit: int = RUN_HISTORY_LIMIT) -> list[ProjectRunHistoryItem]:
    safe_limit = max(1, min(limit, 50))
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT id, project_id, runner, exit_code, timed_out, duration_ms,
                   stdout_preview, stderr_preview, output_truncated, created_at
            FROM project_run_history
            WHERE project_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (project_id, safe_limit),
        ).fetchall()
    return [
        ProjectRunHistoryItem(
            id=row["id"],
            projectId=row["project_id"],
            runner=row["runner"],
            exitCode=row["exit_code"],
            timedOut=bool(row["timed_out"]),
            durationMs=row["duration_ms"],
            stdoutPreview=row["stdout_preview"],
            stderrPreview=row["stderr_preview"],
            outputTruncated=bool(row["output_truncated"]),
            createdAt=row["created_at"],
        )
        for row in rows
    ]


def record_run(result: ProjectRunResponse) -> None:
    stdout_preview, stdout_cut = _truncate(result.stdout, RUN_PREVIEW_LIMIT)
    stderr_preview, stderr_cut = _truncate(result.stderr, RUN_PREVIEW_LIMIT)
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO project_run_history (
                project_id, runner, exit_code, timed_out, duration_ms,
                stdout_preview, stderr_preview, output_truncated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.projectId,
                result.runner,
                result.exitCode,
                int(result.timedOut),
                result.durationMs,
                stdout_preview,
                stderr_preview,
                int(result.outputTruncated or stdout_cut or stderr_cut),
            ),
        )
        connection.commit()


def run_project(project: ProjectResponse) -> ProjectRunResponse:
    if not runner_enabled():
        raise ProjectRunnerDisabled(
            "Project execution is disabled. Set PROJECT_RUNNER_ENABLED=true only for reviewed local code."
        )

    manifests, errors = _manifest_index()
    integration = _integration_for(project, manifests, errors)
    if integration.integrationStatus != "ready":
        raise ProjectManifestError(integration.reason or "Project is not ready for execution.")

    manifest, manifest_path = manifests[project.id]
    if manifest.runner != "python-script-v1":
        raise ProjectManifestError(
            f"{manifest.runner} is preview-only and cannot be executed by the local process runner."
        )

    project_dir, entry_point = _resolve_project_paths(manifest, manifest_path)
    command = [sys.executable, "-B", str(entry_point.relative_to(project_dir))]
    safe_environment = {
        "PATH": os.defpath,
        "PYTHONUNBUFFERED": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    timeout = _timeout_seconds()
    started = time.monotonic()

    try:
        completed = subprocess.run(
            command,
            cwd=project_dir,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=safe_environment,
            shell=False,
            check=False,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        exit_code: int | None = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as error:
        stdout = _timeout_text(error.stdout)
        stderr = _timeout_text(error.stderr)
        exit_code = None
        timed_out = True

    duration_ms = int((time.monotonic() - started) * 1000)
    limit = _output_limit()
    stdout, stdout_truncated = _truncate(stdout, limit)
    stderr, stderr_truncated = _truncate(stderr, limit)

    return ProjectRunResponse(
        projectId=project.id,
        runner=manifest.runner,
        exitCode=exit_code,
        timedOut=timed_out,
        durationMs=duration_ms,
        stdout=stdout,
        stderr=stderr,
        outputTruncated=stdout_truncated or stderr_truncated,
    )
