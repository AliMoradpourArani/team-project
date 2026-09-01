"""Unit coverage for local account and session lifecycle."""

from datetime import UTC, datetime, timedelta

import pytest

from backend.database.connection import connect
from backend.database.init_db import initialize_database
from backend.services import auth


@pytest.fixture()
def auth_db(tmp_path, monkeypatch):
    path = tmp_path / "auth.db"
    monkeypatch.setenv("DATABASE_PATH", str(path))
    monkeypatch.setenv("AUTH_SESSION_HOURS", "8")
    initialize_database(path, seed=True)
    return path


def test_account_authenticate_resolve_and_delete(auth_db):
    auth.create_or_update_account(
        username="hossein",
        password="a-strong-password",
        role="student",
        user_id="hossein",
    )
    principal, token = auth.authenticate("HOSSEIN", "a-strong-password")
    assert principal.user_id == "hossein"
    assert principal.role == "student"
    assert auth.display_name(principal) == "Hossein"
    assert auth.resolve_session(token) == principal

    auth.delete_session(token)
    assert auth.resolve_session(token) is None


def test_password_rotation_revokes_existing_sessions(auth_db):
    auth.create_or_update_account(
        username="hossein",
        password="first-password",
        role="student",
        user_id="hossein",
    )
    _, token = auth.authenticate("hossein", "first-password")

    auth.create_or_update_account(
        username="hossein",
        password="second-password",
        role="student",
        user_id="hossein",
    )
    assert auth.resolve_session(token) is None
    with pytest.raises(PermissionError):
        auth.authenticate("hossein", "first-password")
    assert auth.authenticate("hossein", "second-password")[0].user_id == "hossein"


def test_invalid_account_inputs_fail_closed(auth_db):
    with pytest.raises(ValueError):
        auth.create_or_update_account(
            username="x",
            password="long-enough",
            role="student",
            user_id="hossein",
        )
    with pytest.raises(ValueError):
        auth.create_or_update_account(
            username="new-user",
            password="short",
            role="student",
            user_id="hossein",
        )
    with pytest.raises(ValueError):
        auth.create_or_update_account(
            username="new-user", password="long-enough", role="owner"
        )
    with pytest.raises(ValueError):
        auth.create_or_update_account(
            username="new-user",
            password="long-enough",
            role="student",
            user_id="missing",
        )
    with pytest.raises(PermissionError):
        auth.authenticate("missing", "long-enough")


def test_expired_session_is_removed(auth_db):
    auth.create_or_update_account(
        username="professor", password="professor-pass", role="professor"
    )
    principal, token = auth.authenticate("professor", "professor-pass")
    assert principal.user_id is None
    assert auth.display_name(principal) == "Professor"

    expired = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()
    with connect() as connection, connection:
        connection.execute("UPDATE auth_sessions SET expires_at = ?", (expired,))
    assert auth.resolve_session(token) is None
