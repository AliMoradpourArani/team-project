"""Recurring project-intelligence maintenance for running deployments."""

from __future__ import annotations

import asyncio
import os

from ..schemas.ai_autonomy import AIProgressSyncRequest
from . import ai_autonomy, queries


def enabled() -> bool:
    return os.getenv("AI_AUTOMATION_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}


def interval_seconds() -> int:
    return max(300, int(os.getenv("AI_AUTOMATION_INTERVAL_SECONDS", "3600")))


def run_once() -> dict[str, int]:
    """Refresh health/notifications and optionally apply evidence-backed progress."""
    projects = queries.list_projects()
    refreshed = 0
    progress_changes = 0
    apply_progress = os.getenv("AI_AUTOMATION_APPLY_PROGRESS", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    for project in projects:
        try:
            ai_autonomy.refresh_notifications(project.id, project.userId)
            refreshed += 1
            if apply_progress:
                result = ai_autonomy.sync_progress(
                    AIProgressSyncRequest(projectId=project.id, apply=True), project.userId
                )
                progress_changes += len(result.updatedActivities)
        except (ValueError, LookupError):
            continue
    return {"projectsRefreshed": refreshed, "progressChanges": progress_changes}


async def maintenance_loop() -> None:
    """Run until application shutdown; first tick occurs after one interval."""
    while True:
        await asyncio.sleep(interval_seconds())
        await asyncio.to_thread(run_once)
