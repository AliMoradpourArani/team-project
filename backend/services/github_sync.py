"""Student GitHub connection, repository import, and profile sync service.

Connections and tokens live in the git-ignored SQLite ``github_connections``
table; the student's ``github_username`` is mirrored into the git-tracked
``data/users/<id>.json`` profile. Imported repositories follow the existing
project contract (``data/projects/<slug>.json`` + a ``python-script-v1``
manifest under ``projects/<owner>/<slug>/``) and are synchronised into the
derived database afterwards.
"""

from __future__ import annotations

import json
import logging
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx

from ..database import source_files
from ..database.connection import connect
from ..database.sync_data import sync_source_data
from ..schemas.api import ProjectResponse
from ..schemas.github_editor import GithubImportResponse, GithubRepo, GithubStatus
from ..schemas.project_runner import ProjectManifest
from ..schemas.source_data import ProjectRecord, UserRecord, validate_github_username, validate_slug
from . import project_runner

LOGGER = logging.getLogger(__name__)
GITHUB_API_BASE_URL = "https://api.github.com"
REPOSITORY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
GIT_CLONE_TIMEOUT_SECONDS = 120


@dataclass(frozen=True)
class GithubConnection:
    """A resolved student GitHub connection persisted in ``github_connections``."""

    user_id: str
    github_username: str
    personal_token: str | None
    can_push: bool
    synced_at: str


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _new_client(token: str | None = None, base: str | None = None) -> httpx.Client:
    """Create an authenticated (when a token is provided) GitHub API client."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "forgeflow-student-sync",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return httpx.Client(
        base_url=base or GITHUB_API_BASE_URL,
        headers=headers,
        timeout=15.0,
        follow_redirects=False,
    )


def _slugify_repo(name: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not value:
        value = "project"
    return value[:48]


def _next_available_slug(owner_root: Path, base: str) -> str:
    candidate = base
    counter = 2
    while (
        candidate == "project.json"
        or (owner_root / candidate).exists()
        or (source_files.DATA_ROOT / "projects" / f"{candidate}.json").exists()
    ):
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate


def _clone_url(token: str | None, full_name: str) -> str:
    if token:
        return f"https://{token}@github.com/{full_name}.git"
    return f"https://github.com/{full_name}.git"


def _clone_repository(url: str, dest: Path) -> None:
    """Clone a repository into ``dest``. Overridable by tests via monkeypatching."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--depth", "1", url, str(dest)],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=GIT_CLONE_TIMEOUT_SECONDS,
    )
def _entry_point(project_dir: Path) -> str:
    main_py = project_dir / "main.py"
    if main_py.is_file():
        return "main.py"
    py_files = sorted(
        path
        for path in project_dir.rglob("*.py")
        if ".git" not in path.parts and path.is_file()
    )
    if not py_files:
        raise ValueError("No Python (.py) file found in the cloned repository.")
    return py_files[0].relative_to(project_dir).as_posix()


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _map_repo(payload: dict) -> GithubRepo:
    owner = payload.get("owner") or {}
    return GithubRepo(
        fullName=str(payload.get("full_name") or ""),
        name=str(payload.get("name") or ""),
        owner=str(owner.get("login") or ""),
        htmlUrl=str(payload.get("html_url") or ""),
        language=payload.get("language"),
        defaultBranch=str(payload.get("default_branch") or "main"),
        updatedAt=payload.get("updated_at"),
        private=bool(payload.get("private")),
    )


def _profile_path(user_id: str) -> Path:
    validate_slug(user_id, "user id")
    return source_files.DATA_ROOT / "users" / f"{user_id}.json"


def _apply_profile(user_id: str, github_username: str | None) -> None:
    """Mirror ``github_username`` into the tracked profile, then sync the DB."""
    path = _profile_path(user_id)
    if path.exists():
        data = UserRecord.model_validate(json.loads(path.read_text(encoding="utf-8")))
        data.github_username = github_username
    else:
        data = UserRecord(
            id=user_id,
            display_name=user_id,
            role="Developer",
            github_username=github_username,
        )
    original = path.read_bytes() if path.exists() else None
    try:
        _write_json(path, data.model_dump(mode="json"))
        with connect() as connection:
            sync_source_data(connection)
    except Exception:
        if original is None:
            path.unlink(missing_ok=True)
        else:
            path.write_bytes(original)
        raise


# ---------------------------------------------------------------------------
# Connection persistence
# ---------------------------------------------------------------------------


def get_connection(user_id: str) -> GithubConnection | None:
    validate_slug(user_id, "user id")
    with connect() as connection:
        row = connection.execute(
            "SELECT github_username, personal_token, can_push, synced_at "
            "FROM github_connections WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    if row is None:
        return None
    return GithubConnection(
        user_id=user_id,
        github_username=row["github_username"],
        personal_token=row["personal_token"],
        can_push=bool(row["can_push"]),
        synced_at=row["synced_at"],
    )


def set_connection(user_id: str, github_username: str, personal_token: str | None) -> None:
    validate_slug(user_id, "user id")
    validate_github_username(github_username)
    with connect() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO github_connections "
            "(user_id, github_username, personal_token, can_push, synced_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                user_id,
                github_username,
                personal_token,
                1 if personal_token else 0,
                _utc_now(),
            ),
        )
        connection.commit()


def clear_connection(user_id: str) -> None:
    validate_slug(user_id, "user id")
    with connect() as connection:
        connection.execute(
            "DELETE FROM github_connections WHERE user_id = ?", (user_id,)
        )
        connection.commit()
# ---------------------------------------------------------------------------
# GitHub API interactions
# ---------------------------------------------------------------------------


def _fetch_authenticated_user(token: str) -> tuple[str, str | None]:
    """Verify a token against GET /user, returning (login, avatar_url)."""
    client = _new_client(token)
    try:
        response = client.get("/user")
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as error:
        raise ValueError(
            "Could not verify your GitHub credentials with the provided token."
        ) from error
    return str(payload.get("login") or ""), payload.get("avatar_url")


# ---------------------------------------------------------------------------
# Public service entry points
# ---------------------------------------------------------------------------


def get_status(user_id: str) -> GithubStatus:
    connection = get_connection(user_id)
    if connection is None:
        return GithubStatus(connected=False)
    return GithubStatus(
        connected=True,
        username=connection.github_username,
        syncedAt=connection.synced_at,
        canPush=connection.can_push,
    )


def connect_github(user_id: str, username: str, token: str | None) -> GithubStatus:
    username = username.strip()
    if token:
        login, _avatar = _fetch_authenticated_user(token)
        if not login or login.lower() != username.lower():
            raise ValueError(
                "The provided token does not belong to the given GitHub username."
            )
    else:
        validate_github_username(username)
    set_connection(user_id, username, token)
    _apply_profile(user_id, username)
    connection = get_connection(user_id)
    return GithubStatus(
        connected=True,
        username=connection.github_username,
        syncedAt=connection.synced_at,
        canPush=connection.can_push,
    )


def disconnect_github(user_id: str) -> GithubStatus:
    clear_connection(user_id)
    return GithubStatus(connected=False)


def list_repos(user_id: str) -> list[GithubRepo]:
    connection = get_connection(user_id)
    if connection is None:
        raise ValueError("Connect your GitHub account before listing repositories.")
    client = _new_client(connection.personal_token)
    try:
        if connection.personal_token:
            response = client.get("/user/repos", params={"per_page": 100, "sort": "updated"})
        else:
            response = client.get(
                f"/users/{connection.github_username}/repos",
                params={"per_page": 100, "sort": "updated"},
            )
        response.raise_for_status()
        payloads = response.json()
    except httpx.HTTPError as error:
        raise ValueError("Could not fetch your repositories from GitHub.") from error
    return [_map_repo(payload) for payload in payloads if isinstance(payload, dict)]


def import_repository(user_id: str, full_name: str) -> GithubImportResponse:
    connection = get_connection(user_id)
    if connection is None:
        raise ValueError("Connect your GitHub account before importing a repository.")

    full_name = full_name.strip()
    if not REPOSITORY_PATTERN.fullmatch(full_name):
        raise ValueError("fullName must use the owner/repository form, e.g. octocat/hello.")
    owner, repo_name = full_name.split("/", 1)
    if owner.lower() != connection.github_username.lower():
        raise ValueError("You can only import repositories you own.")

    projects_root = project_runner._projects_root()
    owner_root = projects_root / user_id
    owner_root.mkdir(parents=True, exist_ok=True)
    slug = _next_available_slug(owner_root, _slugify_repo(repo_name))
    dest = owner_root / slug

    try:
        _clone_repository(_clone_url(connection.personal_token, full_name), dest)
    except Exception as error:
        shutil.rmtree(dest, ignore_errors=True)
        raise ValueError(f"Could not clone repository {full_name}.") from error

    entry_point = _entry_point(dest)
    name = _slugify_repo(repo_name)
    description = f"Imported from GitHub: {full_name}"
    technology = ["Python"]

    record = ProjectRecord(
        id=slug,
        owner_id=user_id,
        name=name,
        description=description,
        technology=technology,
        status="active",
    )
    manifest = ProjectManifest(
        id=slug,
        name=name,
        owner_id=user_id,
        description=description,
        technology=technology,
        project_type="cli",
        runner="python-script-v1",
        entry_point=entry_point,
        repository_path=f"projects/{user_id}/{slug}",
    )

    _write_json(
        source_files.DATA_ROOT / "projects" / f"{slug}.json",
        record.model_dump(mode="json"),
    )
    _write_json(dest / "project.json", manifest.model_dump(mode="json"))

    with connect() as connection:
        sync_source_data(connection)

    project = ProjectResponse(
        id=slug,
        userId=user_id,
        name=name,
        description=description,
        technology=technology,
        status="active",
    )
    return GithubImportResponse(
        project=project,
        imported=True,
        repositoryPath=f"projects/{user_id}/{slug}",
        entryPoint=entry_point,
    )
