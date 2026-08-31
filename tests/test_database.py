"""Database foundation tests: migrations from scratch and sync idempotency."""

import sqlite3

import pytest

from backend.database.connection import connect
from backend.database.init_db import apply_migrations, initialize_database
from backend.database.source_files import SourceDataError, load_activities, load_users
from backend.database.sync_data import sync_source_data


def row_count(connection: sqlite3.Connection, table: str) -> int:
    return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_initialize_database_creates_schema_from_scratch(tmp_path):
    database_path = tmp_path / "fresh.db"

    applied = initialize_database(database_path)

    assert applied == [
        "001_create_users",
        "002_create_activities",
        "003_create_projects",
        "004_add_activity_status",
    ]
    with connect(database_path) as connection:
        assert row_count(connection, "schema_migrations") == 4


def test_migrations_are_idempotent(tmp_path):
    database_path = tmp_path / "fresh.db"
    initialize_database(database_path)

    with connect(database_path) as connection:
        assert apply_migrations(connection) == []


def test_sync_is_idempotent(tmp_path):
    database_path = tmp_path / "fresh.db"
    initialize_database(database_path)

    with connect(database_path) as connection:
        first = sync_source_data(connection)
        snapshot = {
            table: connection.execute(f"SELECT * FROM {table}").fetchall()
            for table in ("users", "activities", "projects")
        }
        second = sync_source_data(connection)

        assert first == second
        for table, rows in snapshot.items():
            assert rows == connection.execute(f"SELECT * FROM {table}").fetchall(), table
        assert row_count(connection, "users") == 3
        assert row_count(connection, "activities") == 3
        assert row_count(connection, "projects") == 3


def test_seeded_database_matches_tracked_source_files(tmp_path):
    database_path = tmp_path / "fresh.db"
    initialize_database(database_path, seed=True)

    with connect(database_path) as connection:
        user_ids = {row[0] for row in connection.execute("SELECT id FROM users")}
        activity_ids = {row[0] for row in connection.execute("SELECT id FROM activities")}

    assert user_ids == {user.id for user in load_users()}
    assert activity_ids == {
        activity.id for file in load_activities() for activity in file.activities
    }


def test_activity_ids_are_stable_slugs(tmp_path):
    """Activities must use stable unique ids, not generated integers."""
    initialize_database(tmp_path / "fresh.db", seed=True)

    for file in load_activities():
        for activity in file.activities:
            assert activity.id.startswith(f"{file.user_id}-{file.date}-")


def test_malformed_activity_file_fails_validation(tmp_path, monkeypatch):
    bad_dir = tmp_path / "data" / "activities" / "baduser"
    bad_dir.mkdir(parents=True)
    (bad_dir / "2026-01-01.json").write_text('{"user_id": "baduser"}', encoding="utf-8")

    import backend.database.source_files as source_files

    monkeypatch.setattr(source_files, "DATA_ROOT", tmp_path / "data")

    with pytest.raises(SourceDataError):
        load_activities()


def test_path_traversal_user_id_is_rejected():
    from backend.schemas.source_data import validate_slug

    with pytest.raises(ValueError):
        validate_slug("../../etc/passwd", "user id")
