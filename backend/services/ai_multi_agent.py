"""Provider-backed multi-agent orchestration with deterministic safe fallback."""

from __future__ import annotations

import json
import os
from urllib import error, request

from ..schemas.ai_autonomy import AIOrchestrationResponse
from . import ai_agent, ai_autonomy, ai_workspace

_SPECIALISTS = (
    "planner",
    "project-manager",
    "code-reviewer",
    "debugger",
    "progress-tracker",
    "github-agent",
    "documentation-agent",
)


def _provider_specialist(role: str, context: dict[str, object]) -> str | None:
    api_key = os.getenv("AI_API_KEY", "").strip()
    if not api_key:
        return None
    model = os.getenv("AI_MODEL", "gpt-5-mini").strip() or "gpt-5-mini"
    body = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    f"You are the {role} specialist in a governed software project team. "
                    "Use only the supplied context. Give one concise assessment and one concrete next action. "
                    "Do not claim external actions occurred."
                ),
            },
            {"role": "user", "content": json.dumps(context)},
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
            payload = json.loads(response.read().decode("utf-8"))
        text = str(payload["choices"][0]["message"]["content"]).strip()
        return text[:2000] or None
    except (error.URLError, TimeoutError, KeyError, IndexError, TypeError, ValueError):
        return None


def orchestrate(project_id: str | None, user_id: str) -> AIOrchestrationResponse:
    ai_workspace._project(project_id, user_id)  # noqa: SLF001
    deterministic = ai_agent.multi_agent_review(project_id, user_id)
    health = ai_autonomy.health_score(project_id, user_id)
    snapshot = ai_agent._snapshot(user_id, project_id)  # noqa: SLF001
    context = {
        "project_id": project_id,
        "health": health.model_dump(),
        "progress_percent": snapshot.progressPercent,
        "overdue": [item.model_dump() for item in snapshot.overdueTasks[:8]],
        "github_signals": snapshot.githubSignals,
        "diagnostics": [item.model_dump() for item in snapshot.findings],
    }
    fallback = {item.specialist: item.summary for item in deterministic.results}
    assessments: list[str] = []
    for role in _SPECIALISTS:
        text = _provider_specialist(role, context)
        assessments.append(f"{role}: {text or fallback.get(role, 'No assessment available.')}")

    warning_counts: dict[str, int] = {}
    next_actions: list[str] = []
    for result in deterministic.results:
        for finding in result.findings:
            if finding.severity != "info":
                warning_counts[finding.title] = warning_counts.get(finding.title, 0) + 1
        next_actions.extend(task.title for task in result.suggestedTasks[:2])
    disagreements = [
        f"'{title}' appears in only one specialist finding set and needs coordinator judgment."
        for title, count in warning_counts.items()
        if count == 1
    ][:8]
    return AIOrchestrationResponse(
        projectId=project_id,
        executiveSummary=(
            f"Seven specialists evaluated shared project state with health {health.overall}/100. "
            f"Provider-backed specialists are {'enabled' if os.getenv('AI_API_KEY', '').strip() else 'using deterministic fallback'}."
        ),
        consensus=assessments,
        disagreements=disagreements,
        nextActions=list(dict.fromkeys(next_actions))[:10],
    )
