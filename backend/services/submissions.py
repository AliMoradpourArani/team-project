"""Runtime-only immutable project submissions and professor release manifests."""

from __future__ import annotations

import base64
import hashlib
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from ..database.connection import REPOSITORY_ROOT, connect
from ..schemas.api import ProjectResponse
from ..schemas.submission import (
    ProfessorSubmissionDashboardResponse,
    ProfessorSubmissionItem,
    ProjectSubmissionResponse,
    ProjectSubmissionStatusResponse,
    SubmissionReleaseDetail,
    SubmissionReleaseInput,
    SubmissionReleaseSummary,
    SubmissionSettingsInput,
    SubmissionSettingsResponse,
)
from . import project_reviews, project_runner

MAX_SNAPSHOT_FILES = 300
MAX_SNAPSHOT_BYTES = 5_000_000
MAX_SINGLE_FILE_BYTES = 2_000_000
IGNORED_PARTS = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}
SENSITIVE_FILE_NAMES = {"id_rsa", "id_ed25519", "credentials.json", "secrets.json"}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}


class SubmissionConflict(RuntimeError):
    """Raised when the current submission/release state blocks a mutation."""


def _parse_deadline(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _accepting(is_open: bool, deadline_at: str | None) -> bool:
    if not is_open:
        return False
    deadline = _parse_deadline(deadline_at)
    return deadline is None or datetime.now(UTC) <= deadline


def _settings_from_row(row) -> SubmissionSettingsResponse:
    is_open = bool(row["is_open"])
    return SubmissionSettingsResponse(
        isOpen=is_open,
        deadlineAt=row["deadline_at"],
        acceptingSubmissions=_accepting(is_open, row["deadline_at"]),
        updatedByUsername=row["updated_by_username"],
        updatedAt=row["updated_at"],
    )


def get_settings() -> SubmissionSettingsResponse:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT s.*, a.username AS updated_by_username
            FROM submission_settings AS s
            LEFT JOIN auth_accounts AS a ON a.id = s.updated_by_account_id
            WHERE s.id = 1
            """
        ).fetchone()
    if row is None:
        raise RuntimeError("Submission settings are not initialized.")
    return _settings_from_row(row)


def save_settings(account_id: int, payload: SubmissionSettingsInput) -> SubmissionSettingsResponse:
    deadline = payload.deadlineAt.astimezone(UTC).isoformat() if payload.deadlineAt is not None else None
    with connect() as connection, connection:
        connection.execute(
            """
            UPDATE submission_settings
            SET is_open = ?, deadline_at = ?, updated_by_account_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = 1
            """,
            (1 if payload.isOpen else 0, deadline, account_id),
        )
    return get_settings()


def _submission_from_row(row) -> ProjectSubmissionResponse:
    return ProjectSubmissionResponse(
        id=row["id"],
        projectId=row["project_id"],
        userId=row["user_id"],
        submittedByUsername=row["submitted_by_username"],
        version=row["version"],
        snapshotDigest=row["snapshot_digest"],
        sourceFileCount=row["source_file_count"],
        sourceTotalBytes=row["source_total_bytes"],
        reviewStatus=row["review_status"],
        reviewTotalScore=row["review_total_score"],
        submittedAt=row["submitted_at"],
    )


def get_latest_submission(project_id: str) -> ProjectSubmissionResponse | None:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT s.*, a.username AS submitted_by_username
            FROM project_submissions AS s
            JOIN auth_accounts AS a ON a.id = s.submitted_by_account_id
            WHERE s.project_id = ?
            ORDER BY s.version DESC
            LIMIT 1
            """,
            (project_id,),
        ).fetchone()
    return _submission_from_row(row) if row is not None else None


def _history_count(project_id: str) -> int:
    with connect() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM project_submissions WHERE project_id = ?",
            (project_id,),
        ).fetchone()
    return int(row["count"])


def _blocked_reason(settings: SubmissionSettingsResponse) -> str | None:
    if not settings.isOpen:
        return "Submissions are closed by the professor."
    if not settings.acceptingSubmissions:
        return "The submission deadline has passed."
    return None


def get_project_status(project_id: str) -> ProjectSubmissionStatusResponse:
    settings = get_settings()
    blocked = _blocked_reason(settings)
    return ProjectSubmissionStatusResponse(
        settings=settings,
        latestSubmission=get_latest_submission(project_id),
        historyCount=_history_count(project_id),
        canSubmit=blocked is None,
        blockedReason=blocked,
    )


def _project_directory(repository_path: str) -> Path:
    declared = REPOSITORY_ROOT / repository_path
    if declared.is_symlink():
        raise SubmissionConflict("Symlinked project directories cannot be submitted.")
    project_dir = declared.resolve()
    projects_root = (REPOSITORY_ROOT / "projects").resolve()
    if not project_dir.is_dir() or projects_root not in project_dir.parents:
        raise SubmissionConflict("Project source directory is outside the reviewed projects root.")
    return project_dir


def _looks_sensitive(path: Path) -> bool:
    name = path.name.lower()
    return (
        name.startswith(".env")
        or name in SENSITIVE_FILE_NAMES
        or path.suffix.lower() in SENSITIVE_SUFFIXES
    )


def _source_files(project_dir: Path) -> tuple[list[dict], int]:
    files: list[dict] = []
    total_bytes = 0
    for path in sorted(project_dir.rglob("*")):
        relative = path.relative_to(project_dir)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        if path.is_symlink():
            raise SubmissionConflict(f"Symlinked source path cannot be frozen: {relative.as_posix()}")
        if not path.is_file():
            continue
        if _looks_sensitive(path):
            raise SubmissionConflict(
                f"Potential secret file cannot be frozen: {relative.as_posix()}. Remove it from the project source before submitting."
            )
        if len(files) >= MAX_SNAPSHOT_FILES:
            raise SubmissionConflict(
                f"Project exceeds the submission snapshot limit of {MAX_SNAPSHOT_FILES} files."
            )
        size = path.stat().st_size
        if size > MAX_SINGLE_FILE_BYTES:
            raise SubmissionConflict(
                f"Source file {relative.as_posix()} exceeds the {MAX_SINGLE_FILE_BYTES}-byte snapshot limit."
            )
        total_bytes += size
        if total_bytes > MAX_SNAPSHOT_BYTES:
            raise SubmissionConflict(
                f"Project exceeds the {MAX_SNAPSHOT_BYTES}-byte submission snapshot limit."
            )
        content = path.read_bytes()
        files.append(
            {
                "path": relative.as_posix(),
                "bytes": size,
                "sha256": hashlib.sha256(content).hexdigest(),
                "contentBase64": base64.b64encode(content).decode("ascii"),
            }
        )
    return files, total_bytes


def _build_snapshot(project: ProjectResponse) -> tuple[str, str, int, int, str | None, int | None]:
    detail = project_runner.project_detail(project)
    if detail.integration.integrationStatus != "ready":
        raise SubmissionConflict("Project integration must be ready before submission.")
    if detail.healthPassed != detail.healthTotal:
        raise SubmissionConflict("All project integration health checks must pass before submission.")
    repository_path = detail.integration.repositoryPath
    if repository_path is None:
        raise SubmissionConflict("Integrated project has no repository path.")

    project_dir = _project_directory(repository_path)
    files, total_bytes = _source_files(project_dir)
    review = project_reviews.get_review(project.id)
    snapshot = {
        "schemaVersion": 1,
        "project": project.model_dump(mode="json"),
        "integration": detail.integration.model_dump(mode="json"),
        "health": [item.model_dump(mode="json") for item in detail.health],
        "source": files,
        "review": review.model_dump(mode="json") if review is not None else None,
    }
    encoded = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return (
        digest,
        encoded,
        len(files),
        total_bytes,
        review.status if review is not None else None,
        review.totalScore if review is not None else None,
    )


def submit_project(project: ProjectResponse, account_id: int) -> ProjectSubmissionResponse:
    settings = get_settings()
    blocked = _blocked_reason(settings)
    if blocked is not None:
        raise SubmissionConflict(blocked)

    digest, snapshot_json, file_count, total_bytes, review_status, review_total = _build_snapshot(
        project
    )
    with connect() as connection, connection:
        row = connection.execute(
            "SELECT COALESCE(MAX(version), 0) + 1 AS next_version FROM project_submissions WHERE project_id = ?",
            (project.id,),
        ).fetchone()
        version = int(row["next_version"])
        cursor = connection.execute(
            """
            INSERT INTO project_submissions (
                project_id, user_id, submitted_by_account_id, version, snapshot_digest,
                source_file_count, source_total_bytes, review_status, review_total_score, snapshot_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                project.id,
                project.userId,
                account_id,
                version,
                digest,
                file_count,
                total_bytes,
                review_status,
                review_total,
                snapshot_json,
            ),
        )
        submission_id = int(cursor.lastrowid)
        row = connection.execute(
            """
            SELECT s.*, a.username AS submitted_by_username
            FROM project_submissions AS s
            JOIN auth_accounts AS a ON a.id = s.submitted_by_account_id
            WHERE s.id = ?
            """,
            (submission_id,),
        ).fetchone()
    if row is None:
        raise RuntimeError("Project submission could not be persisted.")
    return _submission_from_row(row)


def get_professor_dashboard(projects: list[ProjectResponse]) -> ProfessorSubmissionDashboardResponse:
    settings = get_settings()
    items = [
        ProfessorSubmissionItem(
            project=project,
            latestSubmission=get_latest_submission(project.id),
            review=project_reviews.get_review(project.id),
        )
        for project in projects
    ]
    submitted = sum(item.latestSubmission is not None for item in items)
    approved = sum(item.review is not None and item.review.status == "approved" for item in items)
    release_ready = bool(items) and submitted == len(items) and approved == len(items)
    if not items:
        release_reason = "No tracked projects are available for release."
    elif submitted != len(items):
        release_reason = f"{len(items) - submitted} project(s) still need a frozen submission."
    elif approved != len(items):
        release_reason = f"{len(items) - approved} project(s) still need an approved professor review."
    else:
        release_reason = None
    return ProfessorSubmissionDashboardResponse(
        settings=settings,
        totalProjects=len(items),
        submittedProjects=submitted,
        pendingProjects=len(items) - submitted,
        approvedProjects=approved,
        releaseReady=release_ready,
        releaseBlockedReason=release_reason,
        items=items,
    )


def _release_summary_from_row(row) -> SubmissionReleaseSummary:
    return SubmissionReleaseSummary(
        id=row["id"],
        label=row["label"],
        manifestDigest=row["manifest_digest"],
        projectCount=row["project_count"],
        createdByUsername=row["created_by_username"],
        createdAt=row["created_at"],
    )


def list_releases() -> list[SubmissionReleaseSummary]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT r.*, a.username AS created_by_username
            FROM submission_releases AS r
            JOIN auth_accounts AS a ON a.id = r.created_by_account_id
            ORDER BY r.id DESC
            """
        ).fetchall()
    return [_release_summary_from_row(row) for row in rows]


def create_release(
    projects: list[ProjectResponse], account_id: int, payload: SubmissionReleaseInput
) -> SubmissionReleaseDetail:
    dashboard = get_professor_dashboard(projects)
    if not dashboard.releaseReady:
        raise SubmissionConflict(dashboard.releaseBlockedReason or "Release is not ready.")

    entries = []
    for item in dashboard.items:
        submission = item.latestSubmission
        review = item.review
        if submission is None or review is None:
            raise SubmissionConflict("Release readiness changed while building the manifest.")
        entries.append(
            {
                "projectId": item.project.id,
                "userId": item.project.userId,
                "projectName": item.project.name,
                "submissionId": submission.id,
                "submissionVersion": submission.version,
                "submissionDigest": submission.snapshotDigest,
                "submittedAt": submission.submittedAt,
                "reviewStatus": review.status,
                "reviewTotalScore": review.totalScore,
                "reviewUpdatedAt": review.updatedAt,
            }
        )

    manifest = {"schemaVersion": 1, "label": payload.label, "projects": entries}
    encoded = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    try:
        with connect() as connection, connection:
            cursor = connection.execute(
                """
                INSERT INTO submission_releases (
                    label, manifest_digest, manifest_json, project_count, created_by_account_id
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (payload.label, digest, encoded, len(entries), account_id),
            )
            release_id = int(cursor.lastrowid)
    except sqlite3.IntegrityError as error:
        if "UNIQUE constraint failed: submission_releases.label" in str(error):
            raise SubmissionConflict("A frozen release with this label already exists.") from error
        raise
    return get_release(release_id)


def get_release(release_id: int) -> SubmissionReleaseDetail:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT r.*, a.username AS created_by_username
            FROM submission_releases AS r
            JOIN auth_accounts AS a ON a.id = r.created_by_account_id
            WHERE r.id = ?
            """,
            (release_id,),
        ).fetchone()
    if row is None:
        raise SubmissionConflict(f"Unknown frozen release: {release_id}")
    summary = _release_summary_from_row(row)
    return SubmissionReleaseDetail(**summary.model_dump(), manifest=json.loads(row["manifest_json"]))
