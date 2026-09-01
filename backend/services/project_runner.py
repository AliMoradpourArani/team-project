"""Controlled local execution for reviewed, allowlisted student projects."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

from pydantic import ValidationError

from ..database.connection import REPOSITORY_ROOT
from ..schemas.api import ProjectResponse
from ..schemas.project_runner import ProjectIntegrationResponse, ProjectManifest, ProjectRunResponse
from ..schemas.source_data import validate_slug

DEFAULT_TIMEOUT_SECONDS = 5
MAX_TIMEOUT_SECONDS = 30
DEFAULT_OUTPUT_LIMIT = 16_000


class ProjectRunnerError(RuntimeError):
    """Base error for manifest discovery and controlled execution."""


class ProjectRunnerDisabled(ProjectRunnerError):
    """Raised when execution is disabled by runtime configuration."""


class ProjectManifestError(ProjectRunnerError):
    """Raised when a project manifest or path violates the runner contract."""


def runner_enabled() -> bool:
    return os.getenv("PROJECT_RUNNER_ENABLED", "false").strip().lower() in {
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
        raise ProjectManifestError("Symlinked project directories are not executable.")

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
            raise ProjectManifestError("Symlinked entry-point paths are not executable.")

    owner_dir = Path(manifest.repository_path).parts[1]
    if owner_dir != manifest.owner_id:
        raise ProjectManifestError("Manifest owner_id must match its projects/<owner>/ directory.")
    return actual_dir, entry_point


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
            reason="No valid projects/<owner>/<project>/project.json manifest is linked to this project.",
        )

    manifest, manifest_path = item
    try:
        if manifest.owner_id != project.userId:
            raise ProjectManifestError("Manifest owner_id does not match authoritative project owner.")
        _resolve_project_paths(manifest, manifest_path)
    except ProjectManifestError as error:
        return ProjectIntegrationResponse(
            projectId=project.id,
            userId=project.userId,
            name=project.name,
            integrationStatus="invalid",
            runnerEnabled=enabled,
            runnable=False,
            projectType=manifest.project_type,
            runner=manifest.runner,
            entryPoint=manifest.entry_point,
            repositoryPath=manifest.repository_path,
            reason=str(error),
        )

    return ProjectIntegrationResponse(
        projectId=project.id,
        userId=project.userId,
        name=project.name,
        integrationStatus="ready",
        runnerEnabled=enabled,
        runnable=enabled,
        projectType=manifest.project_type,
        runner=manifest.runner,
        entryPoint=manifest.entry_point,
        repositoryPath=manifest.repository_path,
        reason=None if enabled else "Runner is disabled. Set PROJECT_RUNNER_ENABLED=true after reviewing project code.",
    )


def list_integrations(projects: list[ProjectResponse]) -> list[ProjectIntegrationResponse]:
    manifests, errors = _manifest_index()
    return [_integration_for(project, manifests, errors) for project in projects]


def _truncate(value: str, limit: int) -> tuple[str, bool]:
    if len(value) <= limit:
        return value, False
    return value[:limit] + "\n[output truncated]", True


def _timeout_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value


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
