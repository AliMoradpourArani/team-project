"""Create or rotate a local student/professor login account."""

from __future__ import annotations

import argparse
import getpass
import os

from ..database.init_db import initialize_database
from ..services.auth import create_or_update_account


def _prompt(value: str | None, label: str) -> str:
    return value.strip() if value else input(f"{label}: ").strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--username")
    parser.add_argument("--role", choices=["student", "professor"])
    parser.add_argument("--user-id")
    parser.add_argument(
        "--password-env",
        default="AUTH_BOOTSTRAP_PASSWORD",
        help="Environment variable containing the password for non-interactive use.",
    )
    args = parser.parse_args()

    initialize_database()
    username = _prompt(args.username, "Username")
    role = args.role or input("Role [student/professor]: ").strip().lower()
    user_id = args.user_id
    if role == "student" and not user_id:
        entered = input(f"Tracked user id [{username}]: ").strip()
        user_id = entered or username

    password = os.getenv(args.password_env, "")
    if not password:
        password = getpass.getpass("Password: ")
        confirmation = getpass.getpass("Confirm password: ")
        if password != confirmation:
            raise SystemExit("Passwords do not match.")

    create_or_update_account(username=username, password=password, role=role, user_id=user_id)
    target = f" -> {user_id}" if user_id else ""
    print(f"Account ready: {username} ({role}){target}")


if __name__ == "__main__":
    main()
