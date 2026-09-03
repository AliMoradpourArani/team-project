"""In-page code editor service: list/read/write project files and commit+push.

File access is bound to the project directory using traversal safeguards. Git
operations run through ``_run_git`` so tests can monkeypatch them and never
invoke a real ``git`` binary.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from ..schemas.api import ProjectResponse
from ..schemas.github_editor import ProjectCommitResponse, ProjectFileEntry, ProjectFileResponse
from . import project_runner
from .github_sync import GithubConnection
from .queries import NotFoundError


class ProjectNotIntegrated(NotFoundError):
    """Raised when a project has no resolvable on-disk repository."""


def _projects_root() -> Path:
    return project_runner._projects_root()


def _resolve_project_dir(project: ProjectResponse) -> Path:
    manifests, _errors = project_runner._manifest_index()
    item = manifests.get(project.id)
    if item is None:
        raise ProjectNotIntegrated(f"Project has no integrated directory: {project.id}")
    manifest, manifest_path = item
    project_dir, _entry = project_runner._resolve_project_paths(manifest, manifest_path)
    return project_dir.resolve()
def _safe_target(project_dir: Path, rel_path: str) -> Path:
    """Resolve a user-supplied relative path inside the project directory."""
    rel_path = rel_path.replace("\\", "/")
    if not rel_path or rel_path == "." or os.path.isabs(rel_path) or rel_path.startswith("/"):
        raise ValueError("File path must be a valid relative path.")
    parts = rel_path.split("/")
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ValueError("File path must not contain traversal segments.")
    if ".git" in parts:
        raise ValueError("File path must not target git internals.")
    target = (project_dir / rel_path).resolve()
    if target != project_dir and project_dir not in target.parents:
        raise ValueError("File path escapes the project directory.")
    return target


def list_files(project: ProjectResponse) -> list[ProjectFileEntry]:
    project_dir = _resolve_project_dir(project)
    entries: list[ProjectFileEntry] = []
    for root, dirnames, filenames in os.walk(project_dir):
        dirnames[:] = sorted(name for name in dirnames if name != ".git" and not name.startswith("."))
        root_path = Path(root)
        relative = root_path.relative_to(project_dir)
        if relative != Path("."):
            entries.append(
                ProjectFileEntry(
                    path=relative.as_posix(),
                    name=relative.name,
                    isDirectory=True,
                    size=0,
                )
            )
        for filename in sorted(filenames):
            file_path = root_path / filename
            entries.append(
                ProjectFileEntry(
                    path=(relative / filename).as_posix(),
                    name=filename,
                    isDirectory=False,
                    size=file_path.stat().st_size,
                )
            )
    entries.sort(key=lambda entry: (entry.path.count("/"), entry.path))
    return entries


def read_file(project: ProjectResponse, path: str) -> ProjectFileResponse:
    project_dir = _resolve_project_dir(project)
    target = _safe_target(project_dir, path)
    if not target.is_file():
        raise NotFoundError(f"No such file in project {project.id}: {path}")
    try:
        content = target.read_text(encoding="utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"File {path} is not valid UTF-8 text.") from error
    return ProjectFileResponse(path=path, content=content, size=target.stat().st_size)


def write_file(project: ProjectResponse, path: str, content: str) -> ProjectFileResponse:
    project_dir = _resolve_project_dir(project)
    target = _safe_target(project_dir, path)
    if target.is_dir():
        raise ValueError(f"Cannot write to a directory: {path}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return ProjectFileResponse(path=path, content=content, size=target.stat().st_size)
def _run_git(project_dir: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a git subcommand inside the project. Overridable by tests."""
    return subprocess.run(
        ["git", "-C", str(project_dir), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )


def _credential_url(origin: str, token: str) -> str:
    clean_origin = re.sub(r"^https://[^@]+@", "https://", origin)
    if clean_origin.startswith("https://"):
        return clean_origin.replace("https://", f"https://x-access-token:{token}@", 1)
    return clean_origin


def _push(project_dir: Path, token: str) -> bool:
    branch = _run_git(project_dir, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    origin = _run_git(project_dir, "remote", "get-url", "origin").stdout.strip()
    if not branch or not origin:
        return False
    result = _run_git(project_dir, "push", _credential_url(origin, token), f"HEAD:{branch}")
    return result.returncode == 0


def commit_and_push(
    project: ProjectResponse,
    message: str,
    connection: GithubConnection | None,
) -> ProjectCommitResponse:
    project_dir = _resolve_project_dir(project)
    _run_git(project_dir, "add", "-A")
    staged = _run_git(project_dir, "diff", "--cached", "--quiet")
    if staged.returncode == 0:
        return ProjectCommitResponse(
            committed=False,
            pushed=False,
            message=message,
            sha=None,
            detail="No changes to commit.",
        )

    commit = _run_git(project_dir, "commit", "-m", message)
    if commit.returncode != 0:
        return ProjectCommitResponse(
            committed=False,
            pushed=False,
            message=message,
            sha=None,
            kind="error",
            detail=(commit.stderr or commit.stdout).strip() or "git commit failed.",
        )

    sha = None
    rev = _run_git(project_dir, "rev-parse", "HEAD")
    if rev.returncode == 0:
        sha = rev.stdout.strip() or None

    can_push = bool(connection and connection.personal_token and connection.can_push)
    if can_push:
        pushed = _push(project_dir, connection.personal_token)
        detail = (
            "Committed and pushed to origin."
            if pushed
            else "Committed locally, but the push to origin failed."
        )
    else:
        pushed = False
        detail = "Committed locally."

    return ProjectCommitResponse(
        committed=True,
        pushed=pushed,
        message=message,
        sha=sha,
        detail=detail,
    )
