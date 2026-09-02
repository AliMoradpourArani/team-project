"""Persistent project copilot threads grounded in workspace and GitHub state."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from ..database.connection import connect
from ..schemas.ai import (
    AIAgentMessage,
    AIAgentReply,
    AIAgentSnapshot,
    AIAgentThread,
    AIAgentThreadCreate,
    AITaskSuggestion,
)
from . import ai_workspace, github_integration, queries


def _owned_project(project_id: str | None, user_id: str):
    return ai_workspace._project(project_id, user_id)  # noqa: SLF001


def _message_from_row(row) -> AIAgentMessage:
    return AIAgentMessage(
        id=row["id"],
        role=row["role"],
        content=row["content"],
        createdAt=row["created_at"],
    )


def _thread(thread_id: str, user_id: str) -> AIAgentThread:
    with connect() as connection:
        row = connection.execute(
            """
            SELECT id, project_id, title, memory, created_at, updated_at
            FROM ai_agent_threads WHERE id = ? AND user_id = ?
            """,
            (thread_id, user_id),
        ).fetchone()
        if row is None:
            raise queries.NotFoundError(f"Unknown AI thread: {thread_id}")
        message_rows = connection.execute(
            """
            SELECT id, role, content, created_at
            FROM ai_agent_messages WHERE thread_id = ? ORDER BY id
            """,
            (thread_id,),
        ).fetchall()
    return AIAgentThread(
        id=row["id"],
        projectId=row["project_id"],
        title=row["title"],
        memory=row["memory"],
        createdAt=row["created_at"],
        updatedAt=row["updated_at"],
        messages=[_message_from_row(item) for item in message_rows],
    )


def list_threads(user_id: str) -> list[AIAgentThread]:
    with connect() as connection:
        rows = connection.execute(
            """
            SELECT id FROM ai_agent_threads
            WHERE user_id = ? ORDER BY updated_at DESC, created_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [_thread(row["id"], user_id) for row in rows]


def create_thread(payload: AIAgentThreadCreate, user_id: str) -> AIAgentThread:
    _owned_project(payload.projectId, user_id)
    thread_id = uuid4().hex
    with connect() as connection, connection:
        connection.execute(
            """
            INSERT INTO ai_agent_threads (id, user_id, project_id, title)
            VALUES (?, ?, ?, ?)
            """,
            (thread_id, user_id, payload.projectId, payload.title),
        )
    return _thread(thread_id, user_id)


def delete_thread(thread_id: str, user_id: str) -> None:
    with connect() as connection, connection:
        cursor = connection.execute(
            "DELETE FROM ai_agent_threads WHERE id = ? AND user_id = ?",
            (thread_id, user_id),
        )
        if cursor.rowcount == 0:
            raise queries.NotFoundError(f"Unknown AI thread: {thread_id}")


def _snapshot(user_id: str, project_id: str | None) -> AIAgentSnapshot:
    activities = [item for item in queries.list_activities() if item.userId == user_id]
    if project_id is not None:
        activities = [item for item in activities if item.projectId == project_id]
    today = date.today().isoformat()
    overdue = [item for item in activities if item.date < today and item.status != "completed"]
    project = _owned_project(project_id, user_id)
    findings = ai_workspace._project_findings(project)  # noqa: SLF001

    github_signals: list[str] = []
    dashboard = github_integration.get_professor_github_dashboard()
    if dashboard.status == "ok":
        for event in dashboard.timeline:
            if event.userId == user_id:
                github_signals.append(f"{event.kind}: {event.title} ({event.detail})")
            if len(github_signals) >= 6:
                break

    return AIAgentSnapshot(
        progressPercent=ai_workspace._progress(user_id, project_id),  # noqa: SLF001
        overdueTasks=overdue[:12],
        githubSignals=github_signals,
        findings=findings,
    )


def _suggested_tasks(thread: AIAgentThread, snapshot: AIAgentSnapshot) -> list[AITaskSuggestion]:
    project_id = thread.projectId
    suggestions: list[AITaskSuggestion] = []
    for item in snapshot.overdueTasks[:4]:
        suggestions.append(
            AITaskSuggestion(
                title=f"Replan overdue: {item.title}",
                date=date.today().isoformat(),
                rationale="This tracked task is overdue and still unfinished.",
                projectId=project_id,
            )
        )
    if snapshot.findings and not suggestions:
        first = snapshot.findings[0]
        suggestions.append(
            AITaskSuggestion(
                title=f"Resolve: {first.title}",
                date=date.today().isoformat(),
                rationale=first.recommendation,
                projectId=project_id,
            )
        )
    return suggestions


def _local_reply(content: str, snapshot: AIAgentSnapshot) -> str:
    parts = [f"Tracked progress is {snapshot.progressPercent}%."]
    if snapshot.overdueTasks:
        parts.append(f"I found {len(snapshot.overdueTasks)} overdue unfinished task(s).")
    if snapshot.githubSignals:
        parts.append("Recent GitHub work is visible, so I can factor implementation activity into replanning.")
    errors = [item for item in snapshot.findings if item.severity == "error"]
    warnings = [item for item in snapshot.findings if item.severity == "warning"]
    if errors:
        parts.append(f"There are {len(errors)} blocking project error(s) to address first.")
    elif warnings:
        parts.append(f"There are {len(warnings)} project warning(s) worth reviewing.")
    else:
        parts.append("No blocking tracked project error is currently visible.")
    parts.append(f"Your request was: {content.strip()}")
    parts.append("I recommend handling blockers and overdue work first, then updating the next milestone.")
    return " ".join(parts)


def post_message(thread_id: str, content: str, user_id: str) -> AIAgentReply:
    thread = _thread(thread_id, user_id)
    snapshot = _snapshot(user_id, thread.projectId)
    reply_text = _local_reply(content, snapshot)
    memory = (
        f"progress={snapshot.progressPercent}%; overdue={len(snapshot.overdueTasks)}; "
        f"github_signals={len(snapshot.githubSignals)}; last_request={content.strip()[:300]}"
    )
    with connect() as connection, connection:
        connection.execute(
            "INSERT INTO ai_agent_messages (thread_id, role, content) VALUES (?, 'user', ?)",
            (thread_id, content.strip()),
        )
        cursor = connection.execute(
            "INSERT INTO ai_agent_messages (thread_id, role, content) VALUES (?, 'assistant', ?)",
            (thread_id, reply_text),
        )
        connection.execute(
            """
            UPDATE ai_agent_threads
            SET memory = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND user_id = ?
            """,
            (memory, thread_id, user_id),
        )
        reply_id = cursor.lastrowid
        reply_row = connection.execute(
            "SELECT id, role, content, created_at FROM ai_agent_messages WHERE id = ?",
            (reply_id,),
        ).fetchone()
    updated = _thread(thread_id, user_id)
    return AIAgentReply(
        thread=updated,
        reply=_message_from_row(reply_row),
        snapshot=snapshot,
        suggestedTasks=_suggested_tasks(updated, snapshot),
    )
