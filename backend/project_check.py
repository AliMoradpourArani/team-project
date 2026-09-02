"""Validate member-project onboarding gates from Git-tracked source."""

from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path

from .database.init_db import initialize_database
from .database.source_files import load_projects
from .schemas.api import ProjectResponse
from .services.project_onboarding import get_onboarding


def _api_project(record) -> ProjectResponse:
    return ProjectResponse(
        id=record.id,
        userId=record.owner_id,
        name=record.name,
        description=record.description,
        technology=record.technology,
        status=record.status,
    )


def _print_report(report) -> None:
    icon = {"ready": "READY", "pending": "PENDING", "invalid": "INVALID"}[report.status]
    print(
        f"[{icon}] {report.projectId} ({report.completedGates}/{report.totalGates} gates)"
    )
    for gate in report.gates:
        mark = "PASS" if gate.passed else "FAIL"
        print(f"  {mark:4}  {gate.label}: {gate.detail}")
        if not gate.passed:
            print(f"        Fix: {gate.remediation}")
    print(f"  Next: {report.nextAction}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", help="Require one tracked project to be fully ready.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when any tracked project is pending as well as invalid.",
    )
    args = parser.parse_args()

    projects = [_api_project(record) for record in load_projects()]
    if args.project_id:
        projects = [project for project in projects if project.id == args.project_id]
        if not projects:
            print(f"Unknown tracked project: {args.project_id}")
            raise SystemExit(2)

    original_database = os.environ.get("DATABASE_PATH")
    try:
        with tempfile.TemporaryDirectory(prefix="team-project-check-") as directory:
            database_path = Path(directory) / "check.db"
            os.environ["DATABASE_PATH"] = str(database_path)
            initialize_database(database_path)
            reports = [get_onboarding(project) for project in projects]
    finally:
        if original_database is None:
            os.environ.pop("DATABASE_PATH", None)
        else:
            os.environ["DATABASE_PATH"] = original_database

    for index, report in enumerate(reports):
        if index:
            print()
        _print_report(report)

    if args.project_id or args.strict:
        failed = any(report.status != "ready" for report in reports)
    else:
        failed = any(report.status == "invalid" for report in reports)

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
