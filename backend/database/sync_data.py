"""Idempotent synchronization from Git-tracked source files into the runtime DB.

The Git-tracked files under ``data/`` are the authoritative shared source; the
SQLite database is a local derived runtime representation. Running this module
multiple times with unchanged repository data produces the same database state
and never duplicates records: every row is upserted by its stable identifier.

Usage::

    python -m backend.database.sync_data
"""

from __future__ import annotations

import argparse
from contextlib import closing

from .connection import connect, get_database_path
from .init_db import initialize_database
from .source_files import load_activities, load_projects, load_users


def sync_source_data(connection) -> dict[str, int]:
    """Upsert all Git-tracked source data. Safe to run repeatedly."""
    counts: dict[str, int] = {}

    users = load_users()
    connection.executemany(
        """
        INSERT INTO users (id, display_name, role) VALUES (?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          display_name = excluded.display_name,
          role = excluded.role
        """,
        [(user.id, user.display_name, user.role) for user in users],
    )
    counts["users"] = len(users)

    projects = load_projects()
    connection.executemany(
        """
        INSERT INTO projects (id, user_id, name, description, technology, status)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          user_id = excluded.user_id,
          name = excluded.name,
          description = excluded.description,
          technology = excluded.technology,
          status = excluded.status
        """,
        [
            (p.id, p.owner_id, p.name, p.description, ",".join(p.technology), p.status)
            for p in projects
        ],
    )
    counts["projects"] = len(projects)

    # Reconciliation: the tracked files are the source of truth, so rows whose
    # source file was deleted must be removed from the derived database too.
    tracked_user_ids = [user.id for user in users]
    if tracked_user_ids:
        placeholders = ",".join("?" for _ in tracked_user_ids)
        connection.execute(f"DELETE FROM users WHERE id NOT IN ({placeholders})", tracked_user_ids)
    else:
        connection.execute("DELETE FROM users")
    tracked_project_ids = [project.id for project in projects]
    if tracked_project_ids:
        placeholders = ",".join("?" for _ in tracked_project_ids)
        connection.execute(
            f"DELETE FROM projects WHERE id NOT IN ({placeholders})", tracked_project_ids
        )
    else:
        connection.execute("DELETE FROM projects")

    activity_rows = [
        (activity.id, file.user_id, file.date, activity.title, activity.status, activity.project_id)
        for file in load_activities()
        for activity in file.activities
    ]
    connection.executemany(
        """
        INSERT INTO activities (id, user_id, date, title, status, project_id)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          user_id = excluded.user_id,
          date = excluded.date,
          title = excluded.title,
          status = excluded.status,
          project_id = excluded.project_id
        """,
        activity_rows,
    )
    counts["activities"] = len(activity_rows)

    # Composite identity of an activity row is (id); compare on (user_id, date)
    # so per-date files that were deleted drop all of their activities.
    tracked_keys = [(row[1], row[2]) for row in activity_rows]
    if not tracked_keys:
        connection.execute("DELETE FROM activities")
    else:
        placeholders = ",".join("(?, ?)" for _ in tracked_keys)
        flat = [value for key in tracked_keys for value in key]
        connection.execute(
            f"DELETE FROM activities WHERE (user_id, date) NOT IN ({placeholders})",
            flat,
        )

    connection.commit()
    return counts


def main() -> None:
    """Apply migrations if needed, then synchronize tracked source data."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=str,
        default=None,
        help="Optional SQLite path. Defaults to backend/database/dev.db or DATABASE_PATH.",
    )
    args = parser.parse_args()

    initialize_database(args.database)
    with closing(connect(args.database)) as connection:
        counts = sync_source_data(connection)

    print(
        "Synchronized source data: "
        + ", ".join(f"{count} {name}" for name, count in counts.items())
    )
    print(f"Database ready: {args.database or get_database_path()}")


if __name__ == "__main__":
    main()
