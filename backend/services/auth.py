"""Local account and server-side session management."""

from __future__ import annotations

import hashlib
import os
import re
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from pwdlib import PasswordHash

from ..database.connection import connect

PASSWORD_HASH = PasswordHash.recommended()
USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]{2,64}$")
AUTH_ROLES = {"student", "professor"}


@dataclass(frozen=True)
class Principal:
    account_id: int
    username: str
    role: str
    user_id: str | None
    csrf_token: str


def session_cookie_name() -> str:
    return os.getenv("AUTH_COOKIE_NAME", "team_session")


def cookie_secure() -> bool:
    return os.getenv("AUTH_COOKIE_SECURE", "false").lower() in {"1", "true", "yes", "on"}


def session_hours() -> int:
    try:
        value = int(os.getenv("AUTH_SESSION_HOURS", "8"))
    except ValueError as exc:
        raise RuntimeError("AUTH_SESSION_HOURS must be an integer") from exc
    return max(1, min(value, 168))


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _now() -> datetime:
    return datetime.now(UTC)


def _normalize_username(username: str) -> str:
    username = username.strip()
    if not USERNAME_RE.fullmatch(username):
        raise ValueError(
            "Username must be 2-64 characters using letters, numbers, dot, dash, or underscore."
        )
    return username


def create_or_update_account(
    *, username: str, password: str, role: str, user_id: str | None = None
) -> None:
    """Create or rotate a local login account without storing credentials in Git data."""
    username = _normalize_username(username)
    role = role.strip().lower()
    if role not in AUTH_ROLES:
        raise ValueError("Role must be 'student' or 'professor'.")
    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters.")

    if role == "student":
        user_id = (user_id or username).strip()
        with connect() as connection:
            exists = connection.execute(
                "SELECT 1 FROM users WHERE id = ?", (user_id,)
            ).fetchone()
        if exists is None:
            raise ValueError(f"Student user does not exist in tracked data: {user_id}")
    else:
        user_id = None

    password_hash = PASSWORD_HASH.hash(password)
    with connect() as connection, connection:
        connection.execute(
            """
            INSERT INTO auth_accounts (username, password_hash, role, user_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                password_hash=excluded.password_hash,
                role=excluded.role,
                user_id=excluded.user_id,
                updated_at=CURRENT_TIMESTAMP
            """,
            (username, password_hash, role, user_id),
        )
        account = connection.execute(
            "SELECT id FROM auth_accounts WHERE username = ? COLLATE NOCASE",
            (username,),
        ).fetchone()
        connection.execute(
            "DELETE FROM auth_sessions WHERE account_id = ?", (account["id"],)
        )


def authenticate(username: str, password: str) -> tuple[Principal, str]:
    """Verify credentials and create a new revocable session."""
    username = _normalize_username(username)
    with connect() as connection:
        row = connection.execute(
            """
            SELECT id, username, password_hash, role, user_id
            FROM auth_accounts WHERE username = ? COLLATE NOCASE
            """,
            (username,),
        ).fetchone()
        if row is None:
            raise PermissionError("Invalid username or password")

        try:
            valid, updated_hash = PASSWORD_HASH.verify_and_update(
                password, row["password_hash"]
            )
        except Exception as exc:  # corrupt/unknown hashes fail closed
            raise PermissionError("Invalid username or password") from exc
        if not valid:
            raise PermissionError("Invalid username or password")

        token = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(24)
        expires_at = _now() + timedelta(hours=session_hours())
        with connection:
            connection.execute(
                "DELETE FROM auth_sessions WHERE expires_at <= ?", (_now().isoformat(),)
            )
            if updated_hash:
                connection.execute(
                    "UPDATE auth_accounts SET password_hash = ?, updated_at=CURRENT_TIMESTAMP WHERE id = ?",
                    (updated_hash, row["id"]),
                )
            connection.execute(
                """
                INSERT INTO auth_sessions (token_hash, account_id, csrf_token, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (_token_hash(token), row["id"], csrf_token, expires_at.isoformat()),
            )

    return (
        Principal(
            account_id=row["id"],
            username=row["username"],
            role=row["role"],
            user_id=row["user_id"],
            csrf_token=csrf_token,
        ),
        token,
    )


def resolve_session(token: str) -> Principal | None:
    if not token:
        return None
    token_hash = _token_hash(token)
    with connect() as connection:
        row = connection.execute(
            """
            SELECT a.id, a.username, a.role, a.user_id, s.csrf_token, s.expires_at
            FROM auth_sessions AS s
            JOIN auth_accounts AS a ON a.id = s.account_id
            WHERE s.token_hash = ?
            """,
            (token_hash,),
        ).fetchone()
        if row is None:
            return None
        expires_at = datetime.fromisoformat(row["expires_at"])
        if expires_at <= _now():
            with connection:
                connection.execute(
                    "DELETE FROM auth_sessions WHERE token_hash = ?", (token_hash,)
                )
            return None

    return Principal(
        account_id=row["id"],
        username=row["username"],
        role=row["role"],
        user_id=row["user_id"],
        csrf_token=row["csrf_token"],
    )


def delete_session(token: str) -> None:
    if not token:
        return
    with connect() as connection, connection:
        connection.execute(
            "DELETE FROM auth_sessions WHERE token_hash = ?", (_token_hash(token),)
        )


def display_name(principal: Principal) -> str:
    if principal.role == "professor":
        return "Professor"
    with connect() as connection:
        row = connection.execute(
            "SELECT display_name FROM users WHERE id = ?", (principal.user_id,)
        ).fetchone()
    return row["display_name"] if row else principal.username
