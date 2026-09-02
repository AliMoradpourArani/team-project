"""AI workspace service with provider-backed and deterministic local modes."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from urllib import error, request

from ..schemas.ai import (
    AIFinding,
    AIModelOutput,
    AIRoadmapMilestone,
    AITaskSuggestion,
    AIWorkspaceRequest,
    AIWorkspaceResponse,
)
from ..schemas.api import ActivityWrite, ProjectResponse
from . import activity_writes, project_runner, queries


def _project(project_id: str | None, user_id: str) -> ProjectResponse | None:
    if project_id is None:
        return None
    project = next((item for item in queries.list_projects() if item.id == project_id), None)
    if project is None or project.userId != user_id:
        raise queries.NotFoundError(f"Unknown or inaccessible project: {project_id}")
    return project


def _progress(user_id: str, project_id: str | None) -> int:
    activities = [item for item in queries.list_activities() if item.userId == user_id]
    if project_id is not None:
        activities = [item for item in activities if item.projectId == project_id]
    if not activities:
        return 0
    weights = {"planned": 0, "in-progress": 50, "completed": 100}
    return round(sum(weights.get(item.status, 0) for item in activities) / len(activities))


def _project_findings(project: ProjectResponse | None) -> list[AIFinding]:
    if project is None:
        return []
    try:
        detail = project_runner.project_detail(project)
    except project_runner.ProjectRunnerError as exc:
        return [
            AIFinding(
                severity="error",
                title="Project integration could not be inspected",
                detail=str(exc),
                recommendation="Fix the project manifest/integration, then run the AI review again.",
            )
        ]

    findings: list[AIFinding] = []
    for check in detail.health:
        if not check.passed:
            findings.append(
                AIFinding(
                    severity="warning",
                    title=check.label,
                    detail=check.detail,
                    recommendation="Resolve this project health check before the next submission.",
                )
            )
    for run in detail.recentRuns[:3]:
        if run.timedOut or (run.exitCode is not None and run.exitCode != 0):
            detail_text = run.stderrPreview.strip() or run.stdoutPreview.strip() or "The project run failed without output."
            findings.append(
                AIFinding(
                    severity="error",
                    title="Recent project run failed",
                    detail=detail_text[:2000],
                    recommendation="Reproduce the failure locally, address the first actionable error, and run the project again.",
                )
            )
    if not findings:
        findings.append(
            AIFinding(
                severity="info",
                title="No current project errors detected",
                detail="The tracked integration checks and recent run history do not show a blocking error.",
                recommendation="Keep tests, documentation, and milestone tasks current as the implementation changes.",
            )
        )
    return findings


def _local_output(payload: AIWorkspaceRequest, user_id: str, project: ProjectResponse | None) -> AIModelOutput:
    current_progress = _progress(user_id, payload.projectId)
    today = date.today()
    subject = project.name if project else "your workspace"
    goal = payload.goal.strip() or (project.description if project else "move the current work toward completion")

    task_templates = [
        f"Define the next measurable outcome for {subject}",
        f"Break {goal[:80]} into an implementation slice",
        f"Implement and verify the highest-priority slice for {subject}",
        f"Review errors, edge cases, and integration health for {subject}",
        f"Document progress and prepare the next checkpoint for {subject}",
        f"Add or update automated tests for {subject}",
        f"Review unfinished work and remove blockers for {subject}",
        f"Prepare a demo or evidence of completed work for {subject}",
    ]
    tasks = [
        AITaskSuggestion(
            title=task_templates[index % len(task_templates)],
            date=(today + timedelta(days=index)).isoformat(),
            rationale="Generated from current project metadata and tracked activity progress.",
            projectId=payload.projectId,
        )
        for index in range(payload.taskCount)
    ]

    roadmap: list[AIRoadmapMilestone] = []
    for index, (title, objective) in enumerate(
        [
            ("Scope", "Turn the goal into a small, testable definition of done."),
            ("Build", "Implement the core path and keep the project runnable."),
            ("Validate", "Test behavior, inspect failures, and close quality gaps."),
            ("Ship", "Document the result and prepare a reviewable submission or demo."),
        ]
    ):
        roadmap.append(
            AIRoadmapMilestone(
                title=title,
                objective=objective,
                targetDate=(today + timedelta(days=(index + 1) * 7)).isoformat(),
                tasks=[item.title for item in tasks[index::4]][:4],
            )
        )

    findings = _project_findings(project) if payload.action in {"debug", "review", "progress"} else []
    action_summary = {
        "plan": f"Created an actionable plan for {subject} based on the current workspace state.",
        "roadmap": f"Created a four-stage roadmap for {subject} with dated milestones.",
        "progress": f"Tracked progress for {subject} from existing activities and project health.",
        "debug": f"Inspected tracked health checks and recent run failures for {subject}.",
        "review": f"Reviewed {subject} for unfinished work, integration issues, and recent execution errors.",
    }
    return AIModelOutput(
        summary=action_summary[payload.action],
        progressPercent=current_progress,
        tasks=tasks if payload.action in {"plan", "roadmap", "progress"} else [],
        roadmap=roadmap if payload.action in {"roadmap", "plan"} else [],
        findings=findings,
    )


def _provider_output(payload: AIWorkspaceRequest, user_id: str, project: ProjectResponse | None) -> tuple[AIModelOutput, str, str | None]:
    api_key = os.getenv("AI_API_KEY", "").strip()
    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("AI_MODEL", "gpt-5-mini").strip() or "gpt-5-mini"
    if not api_key:
        return _local_output(payload, user_id, project), "local", "AI_API_KEY is not configured; using the local planning engine."

    context = {
        "user_id": user_id,
        "action": payload.action,
        "goal": payload.goal,
        "task_count": payload.taskCount,
        "progress_percent": _progress(user_id, payload.projectId),
        "project": project.model_dump() if project else None,
        "activities": [
            item.model_dump()
            for item in queries.list_activities()
            if item.userId == user_id and (payload.projectId is None or item.projectId == payload.projectId)
        ][-30:],
        "diagnostics": [item.model_dump() for item in _project_findings(project)],
    }
    schema_hint = {
        "summary": "string",
        "progressPercent": "integer 0-100",
        "tasks": [{"title": "string", "date": "YYYY-MM-DD", "rationale": "string", "projectId": payload.projectId}],
        "roadmap": [{"title": "string", "objective": "string", "targetDate": "YYYY-MM-DD", "tasks": ["string"]}],
        "findings": [{"severity": "info|warning|error", "title": "string", "detail": "string", "recommendation": "string"}],
    }
    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are the project copilot inside a team workspace. Return only valid JSON matching the requested shape. Be concrete, concise, and grounded only in supplied project data.",
            },
            {
                "role": "user",
                "content": json.dumps({"context": context, "response_shape": schema_hint}),
            },
        ],
        "response_format": {"type": "json_object"},
    }
    req = request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=float(os.getenv("AI_TIMEOUT_SECONDS", "20"))) as response:
            response_body = json.loads(response.read().decode("utf-8"))
        content = response_body["choices"][0]["message"]["content"]
        return AIModelOutput.model_validate(json.loads(content)), "provider", None
    except (error.URLError, TimeoutError, KeyError, ValueError, json.JSONDecodeError) as exc:
        fallback = _local_output(payload, user_id, project)
        return fallback, "local", f"AI provider failed ({type(exc).__name__}); using the local planning engine."


def run_workspace(payload: AIWorkspaceRequest, user_id: str) -> AIWorkspaceResponse:
    project = _project(payload.projectId, user_id)
    output, provider, provider_message = _provider_output(payload, user_id, project)
    applied = []
    if payload.applyTasks and payload.action in {"plan", "roadmap", "progress"}:
        for task in output.tasks:
            applied.append(
                activity_writes.create_activity(
                    ActivityWrite(
                        userId=user_id,
                        date=task.date,
                        title=task.title,
                        status="planned",
                        projectId=task.projectId,
                    )
                )
            )
    return AIWorkspaceResponse(
        action=payload.action,
        provider=provider,
        model=os.getenv("AI_MODEL") if provider == "provider" else None,
        providerMessage=provider_message,
        appliedActivities=applied,
        **output.model_dump(),
    )
