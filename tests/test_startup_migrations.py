"""A database created before newer migrations must self-heal on server startup."""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.database import source_files
from backend.database.connection import REPOSITORY_ROOT
from backend.database.init_db import initialize_database
from backend.services import github_sync


def _isolated_db(tmp_path: Path, monkeypatch) -> Path:
    data_root = tmp_path / "data"
    shutil.copytree(REPOSITORY_ROOT / "data", data_root)
    monkeypatch.setattr(source_files, "DATA_ROOT", data_root)
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("AI_AUTOMATION_ENABLED", "false")
    initialize_database(db_path, seed=True)
    return db_path


def _make_stale(db_path: Path) -> None:
    """Simulate a dev database created before 013 landed."""
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("DROP TABLE github_connections")
        connection.execute(
            "DELETE FROM schema_migrations WHERE version = '013_create_github_connections'"
        )
        connection.commit()
    finally:
        connection.close()


def _has_github_connections(db_path: Path) -> bool:
    connection = sqlite3.connect(db_path)
    try:
        return (
            connection.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name = 'github_connections'"
            ).fetchone()
            is not None
        )
    finally:
        connection.close()


def test_initialize_database_repairs_missing_github_connections(tmp_path, monkeypatch):
    db_path = _isolated_db(tmp_path, monkeypatch)
    _make_stale(db_path)
    assert not _has_github_connections(db_path)

    applied = initialize_database(db_path)

    assert "013_create_github_connections" in applied
    assert _has_github_connections(db_path)
    assert github_sync.get_status("ali").connected is False


def test_server_startup_applies_pending_migrations(tmp_path, monkeypatch):
    db_path = _isolated_db(tmp_path, monkeypatch)
    _make_stale(db_path)
    assert not _has_github_connections(db_path)

    with TestClient(app):
        assert _has_github_connections(db_path)
