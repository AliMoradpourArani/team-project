"""Persistent AI project agent grounded in workspace, memory, diagnostics, and GitHub state."""

from __future__ import annotations

import json
import os
from datetime import date
from urllib import error, request
from uuid import uuid4

from ..database.connection import connect
from ..schemas.ai import (
    AIDailyBrief,
    AIFinding,
    AIGitHubLink,
    AIGitHubLinkWrite,
    AIMemoryItem,
    AIMemoryWrite,
    AIMultiAgentReview,
    AIAgentMessage,
    AIAgentReply,
    AIAgentReplanRequest,
    AIAgentReplanResponse,
    AIAgentSnapshot,
    AIAgentThread,
    AIAgentThreadCreate,
    AISpecialistResult,
    AITaskSuggestion,
    AIWorkspaceRequest,
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


def _github_signals(user_id: str) -> list[str]:
    signals: list[str] = []
    dashboard = github_integration.get_professor_github_dashboard()
    if dashboard.status == "ok":
        for event in dashboard.timeline:
            if event.userId == user_id:
                signals.append(f"{event.kind}: {event.title} ({event.detail})")
            if len(signals) >= 10:
                break
    return signals


def _snapshot(user_id: str, project_id: str | None) -> AIAgentSnapshot:
    activities = [item for item in queries.list_activities() if item.userId == user_id]
    if project_id is not None:
        activities = [item for item in activities if item.projectId == project_id]
    today = date.today().isoformat()
    overdue = [item for item in activities if item.date < today and item.status != "completed"]
    project = _owned_project(project_id, user_id)
    findings = ai_workspace._project_findings(project)  # noqa: SLF001
    return AIAgentSnapshot(
        progressPercent=ai_workspace._progress(user_id, project_id),  # noqa: SLF001
        overdueTasks=overdue[:12],
        githubSignals=_github_signals(user_id),
        findings=findings,
    )


def get_snapshot(thread_id: str, user_id: str) -> AIAgentSnapshot:
    thread = _thread(thread_id, user_id)
    return _snapshot(user_id, thread.projectId)


def _suggested_tasks(thread: AIAgentThread, snapshot: AIAgentSnapshot) -> list[AITaskSuggestion]:
    suggestions: list[AITaskSuggestion] = []
    for item in snapshot.overdueTasks[:4]:
        suggestions.append(
            AITaskSuggestion(
                title=f"Replan overdue: {item.title}",
                date=date.today().isoformat(),
                rationale="This tracked task is overdue and still unfinished.",
                projectId=thread.projectId,
            )
        )
    for finding in snapshot.findings:
        if finding.severity in {"error", "warning"} and len(suggestions) < 6:
            suggestions.append(
                AITaskSuggestion(
                    title=f"Resolve: {finding.title}",
                    date=date.today().isoformat(),
                    rationale=finding.recommendation,
                    projectId=thread.projectId,
                )
            )
    return suggestions


def _local_reply(content: str, snapshot: AIAgentSnapshot) -> str:
    parts = [f"Tracked progress is {snapshot.progressPercent}%."]
    if snapshot.overdueTasks:
        parts.append(f"I found {len(snapshot.overdueTasks)} overdue unfinished task(s).")
    if snapshot.githubSignals:
        parts.append("Recent GitHub evidence is available and included in my project context.")
    blockers = [item for item in snapshot.findings if item.severity == "error"]
    warnings = [item for item in snapshot.findings if item.severity == "warning"]
    if blockers:
        parts.append(f"There are {len(blockers)} blocking project error(s) to address first.")
    elif warnings:
        parts.append(f"There are {len(warnings)} project warning(s) worth reviewing.")
    else:
        parts.append("No blocking tracked project error is currently visible.")
    parts.append(f"Your request was: {content.strip()}")
    parts.append("Prioritize blockers, overdue work, then the next measurable milestone.")
    return " ".join(parts)


def _structured_memory(user_id: str, project_id: str | None) -> dict[str, str]:
    with connect() as connection:
        if project_id is None:
            rows = connection.execute(
                """
                SELECT memory_key, memory_value FROM ai_project_memory
                WHERE user_id = ? AND project_id IS NULL ORDER BY updated_at DESC
                """,
                (user_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT memory_key, memory_value FROM ai_project_memory
                WHERE user_id = ? AND project_id = ? ORDER BY updated_at DESC
                """,
                (user_id, project_id),
            ).fetchall()
    return {row["memory_key"]: row["memory_value"] for row in rows}


def _provider_reply(
    content: str,
    thread: AIAgentThread,
    snapshot: AIAgentSnapshot,
    user_id: str,
) -> tuple[str, str, str | None, str | None]:
    api_key = os.getenv("AI_API_KEY", "").strip()
    model = os.getenv("AI_MODEL", "gpt-5-mini").strip() or "gpt-5-mini"
    if not api_key:
        return _local_reply(content, snapshot), "local", None, "AI_API_KEY is not configured."

    project = _owned_project(thread.projectId, user_id)
    context = {
        "project": project.model_dump() if project else None,
        "thread_memory": thread.memory,
        "structured_memory": _structured_memory(user_id, thread.projectId),
        "progress_percent": snapshot.progressPercent,
        "overdue_tasks": [item.model_dump() for item in snapshot.overdueTasks],
        "github_signals": snapshot.githubSignals,
        "diagnostics": [item.model_dump() for item in snapshot.findings],
        "recent_messages": [item.model_dump() for item in thread.messages[-12:]],
    }
    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a project-management and engineering copilot. Use only supplied context. "
                    "Be concise and actionable. Never claim an external action happened unless the "
                    "context proves it. Treat task mutation as requiring explicit user approval."
                ),
            },
            {"role": "user", "content": json.dumps({"context": context, "request": content})},
        ],
    }
    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    req = request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=float(os.getenv("AI_TIMEOUT_SECONDS", "20"))) as response:
            response_body = json.loads(response.read().decode("utf-8"))
        reply = str(response_body["choices"][0]["message"]["content"]).strip()
        if not reply:
            raise ValueError("Provider returned an empty response")
        return reply[:8000], "openai-compatible", model, None
    except (error.URLError, TimeoutError, KeyError, IndexError, TypeError, ValueError) as exc:
        return (
            _local_reply(content, snapshot),
            "local",
            None,
            f"AI provider failed ({type(exc).__name__}); local agent used.",
        )


def post_message(thread_id: str, content: str, user_id: str) -> AIAgentReply:
    thread = _thread(thread_id, user_id)
    snapshot = _snapshot(user_id, thread.projectId)
    reply_text, provider, model, provider_message = _provider_reply(
        content, thread, snapshot, user_id
    )
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
        reply_row = connection.execute(
            "SELECT id, role, content, created_at FROM ai_agent_messages WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    updated = _thread(thread_id, user_id)
    return AIAgentReply(
        thread=updated,
        reply=_message_from_row(reply_row),
        snapshot=snapshot,
        suggestedTasks=_suggested_tasks(updated, snapshot),
        provider=provider,
        model=model,
        providerMessage=provider_message,
    )


def replan(
    thread_id: str,
    payload: AIAgentReplanRequest,
    user_id: str,
) -> AIAgentReplanResponse:
    thread = _thread(thread_id, user_id)
    before = _snapshot(user_id, thread.projectId)
    blockers = ", ".join(item.title for item in before.findings if item.severity != "info")
    result = ai_workspace.run_workspace(
        AIWorkspaceRequest(
            action="plan",
            projectId=thread.projectId,
            goal=(
                f"Replan current work. Overdue tasks: {len(before.overdueTasks)}. "
                f"Known blockers: {blockers or 'none'}. Use the next measurable outcomes."
            ),
            taskCount=payload.taskCount,
            applyTasks=payload.applyTasks,
        ),
        user_id,
    )
    return AIAgentReplanResponse(
        summary=result.summary,
        tasks=result.tasks,
        appliedActivities=result.appliedActivities,
        snapshot=_snapshot(user_id, thread.projectId),
    )


def list_memory(project_id: str | None, user_id: str) -> list[AIMemoryItem]:
    _owned_project(project_id, user_id)
    with connect() as connection:
        if project_id is None:
            rows = connection.execute(
                """
                SELECT id, memory_key, memory_value, created_at, updated_at
                FROM ai_project_memory WHERE user_id = ? AND project_id IS NULL
                ORDER BY updated_at DESC
                """,
                (user_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT id, memory_key, memory_value, created_at, updated_at
                FROM ai_project_memory WHERE user_id = ? AND project_id = ?
                ORDER BY updated_at DESC
                """,
                (user_id, project_id),
            ).fetchall()
    return [
        AIMemoryItem(
            id=row["id"],
            key=row["memory_key"],
            value=row["memory_value"],
            createdAt=row["created_at"],
            updatedAt=row["updated_at"],
        )
        for row in rows
    ]


def upsert_memory(project_id: str | None, payload: AIMemoryWrite, user_id: str) -> AIMemoryItem:
    _owned_project(project_id, user_id)
    with connect() as connection, connection:
        if project_id is None:
            row = connection.execute(
                """
                SELECT id FROM ai_project_memory
                WHERE user_id = ? AND project_id IS NULL AND memory_key = ?
                """,
                (user_id, payload.key),
            ).fetchone()
        else:
            row = connection.execute(
                """
                SELECT id FROM ai_project_memory
                WHERE user_id = ? AND project_id = ? AND memory_key = ?
                """,
                (user_id, project_id, payload.key),
            ).fetchone()
        if row is None:
            cursor = connection.execute(
                """
                INSERT INTO ai_project_memory (user_id, project_id, memory_key, memory_value)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, project_id, payload.key, payload.value),
            )
            memory_id = cursor.lastrowid
        else:
            memory_id = row["id"]
            connection.execute(
                """
                UPDATE ai_project_memory SET memory_value = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ?
                """,
                (payload.value, memory_id, user_id),
            )
        memory_row = connection.execute(
            """
            SELECT id, memory_key, memory_value, created_at, updated_at
            FROM ai_project_memory WHERE id = ? AND user_id = ?
            """,
            (memory_id, user_id),
        ).fetchone()
    return AIMemoryItem(
        id=memory_row["id"],
        key=memory_row["memory_key"],
        value=memory_row["memory_value"],
        createdAt=memory_row["created_at"],
        updatedAt=memory_row["updated_at"],
    )


def link_github(project_id: str | None, payload: AIGitHubLinkWrite, user_id: str) -> AIGitHubLink:
    _owned_project(project_id, user_id)
    activity = next(
        (
            item
            for item in queries.list_activities()
            if item.id == payload.activityId and item.userId == user_id
        ),
        None,
    )
    if activity is None or (project_id is not None and activity.projectId != project_id):
        raise queries.NotFoundError(f"Unknown or inaccessible activity: {payload.activityId}")
    with connect() as connection, connection:
        cursor = connection.execute(
            """
            INSERT INTO ai_github_links (user_id, project_id, activity_id, kind, reference)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, project_id, payload.activityId, payload.kind, payload.reference),
        )
        row = connection.execute(
            """
            SELECT id, activity_id, kind, reference, created_at
            FROM ai_github_links WHERE id = ? AND user_id = ?
            """,
            (cursor.lastrowid, user_id),
        ).fetchone()
    return AIGitHubLink(
        id=row["id"],
        activityId=row["activity_id"],
        kind=row["kind"],
        reference=row["reference"],
        createdAt=row["created_at"],
    )


def list_github_links(project_id: str | None, user_id: str) -> list[AIGitHubLink]:
    _owned_project(project_id, user_id)
    with connect() as connection:
        if project_id is None:
            rows = connection.execute(
                """
                SELECT id, activity_id, kind, reference, created_at
                FROM ai_github_links WHERE user_id = ? ORDER BY created_at DESC
                """,
                (user_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT id, activity_id, kind, reference, created_at
                FROM ai_github_links WHERE user_id = ? AND project_id = ? ORDER BY created_at DESC
                """,
                (user_id, project_id),
            ).fetchall()
    return [
        AIGitHubLink(
            id=row["id"],
            activityId=row["activity_id"],
            kind=row["kind"],
            reference=row["reference"],
            createdAt=row["created_at"],
        )
        for row in rows
    ]


def daily_brief(project_id: str | None, user_id: str) -> AIDailyBrief:
    project = _owned_project(project_id, user_id)
    snapshot = _snapshot(user_id, project_id)
    blockers = [item.title for item in snapshot.findings if item.severity in {"error", "warning"}]
    priorities = [item.title for item in snapshot.overdueTasks[:3]]
    if not priorities:
        priorities = [task.title for task in _suggested_tasks(
            AIAgentThread(
                id="brief",
                projectId=project_id,
                title="brief",
                memory="",
                createdAt="",
                updatedAt="",
            ),
            snapshot,
        )[:3]]
    subject = project.name if project else "Workspace"
    return AIDailyBrief(
        projectId=project_id,
        headline=f"{subject}: {snapshot.progressPercent}% tracked progress",
        progressPercent=snapshot.progressPercent,
        overdueCount=len(snapshot.overdueTasks),
        githubSignalCount=len(snapshot.githubSignals),
        blockers=blockers[:10],
        priorities=priorities[:8],
    )


def multi_agent_review(project_id: str | None, user_id: str) -> AIMultiAgentReview:
    project = _owned_project(project_id, user_id)
    snapshot = _snapshot(user_id, project_id)
    project_name = project.name if project else "workspace"
    suggestions = _suggested_tasks(
        AIAgentThread(
            id="review",
            projectId=project_id,
            title="review",
            memory="",
            createdAt="",
            updatedAt="",
        ),
        snapshot,
    )
    specialists = [
        ("planner", f"Plan the next measurable slice for {project_name}.", []),
        (
            "project-manager",
            f"Track {len(snapshot.overdueTasks)} overdue item(s) and milestone risk.",
            snapshot.findings,
        ),
        (
            "code-reviewer",
            "Review project health checks and recent execution evidence before accepting work.",
            snapshot.findings,
        ),
        (
            "debugger",
            "Prioritize the first actionable failing health or run diagnostic.",
            [item for item in snapshot.findings if item.severity != "info"],
        ),
        (
            "progress-tracker",
            f"Tracked activity progress is {snapshot.progressPercent}% with GitHub evidence available.",
            [],
        ),
        (
            "github-agent",
            f"Observed {len(snapshot.githubSignals)} recent GitHub signal(s).",
            [],
        ),
        (
            "documentation-agent",
            "Capture decisions, evidence, and definition of done in structured project memory.",
            [],
        ),
    ]
    results = [
        AISpecialistResult(
            specialist=name,
            summary=summary,
            findings=findings[:20],
            suggestedTasks=suggestions[:4] if name in {"planner", "project-manager"} else [],
        )
        for name, summary, findings in specialists
    ]
    executive = (
        f"Seven specialist agents reviewed {project_name}. Progress is {snapshot.progressPercent}%, "
        f"with {len(snapshot.overdueTasks)} overdue task(s), {len(snapshot.githubSignals)} GitHub "
        f"signal(s), and {len([item for item in snapshot.findings if item.severity != 'info'])} "
        "actionable project finding(s)."
    )
    return AIMultiAgentReview(projectId=project_id, results=results, executiveSummary=executive)
