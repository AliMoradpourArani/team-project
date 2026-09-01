"""Query services separating API routes from database access."""

from __future__ import annotations

from ..database.connection import connect
from ..schemas.api import ActivityResponse, ProjectResponse, UserResponse
from ..schemas.source_data import validate_slug


class NotFoundError(LookupError):
    """Raised when a requested resource does not exist (mapped to HTTP 404)."""


def list_users() -> list[UserResponse]:
    with connect() as connection:
        rows = connection.execute(
            "SELECT id, display_name, role, github_username FROM users ORDER BY id"
        ).fetchall()
    return [
        UserResponse(
            id=row["id"],
            name=row["display_name"],
            role=row["role"],
            githubUsername=row["github_username"],
        )
        for row in rows
    ]


def get_user(user_id: str) -> UserResponse:
    validate_slug(user_id, "user id")
    with connect() as connection:
        row = connection.execute(
            "SELECT id, display_name, role, github_username FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    if row is None:
        raise NotFoundError(f"Unknown user: {user_id}")
    return UserResponse(
        id=row["id"],
        name=row["display_name"],
        role=row["role"],
        githubUsername=row["github_username"],
    )


def list_activities() -> list[ActivityResponse]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT id, user_id, date, title, status, project_id
            FROM activities ORDER BY date, id
            """
        ).fetchall()
    return [
        ActivityResponse(
            id=row["id"],
            userId=row["user_id"],
            date=row["date"],
            title=row["title"],
            status=row["status"],
            projectId=row["project_id"],
        )
        for row in rows
    ]


def list_projects() -> list[ProjectResponse]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT id, user_id, name, description, technology, status
            FROM projects ORDER BY id
            """
        ).fetchall()
    return [
        ProjectResponse(
            id=row["id"],
            userId=row["user_id"],
            name=row["name"],
            description=row["description"],
            technology=[item for item in row["technology"].split(",") if item],
            status=row["status"],
        )
        for row in rows
    ]


def user_exists(user_id: str) -> bool:
    try:
        get_user(user_id)
    except (NotFoundError, ValueError):
        return False
    return True
