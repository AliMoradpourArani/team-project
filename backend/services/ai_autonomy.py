"""Repository RAG, governed actions, progress inference, health, debugging, and automation."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from collections import defaultdict, deque
from datetime import date
from pathlib import Path
from urllib import error, parse, request

from ..database.connection import REPOSITORY_ROOT, connect
from ..schemas.ai_autonomy import (
    AIActionProposalRequest,
    AIActionRecord,
    AIDebugResponse,
    AIHealthScore,
    AIMemorySearchResponse,
    AINotification,
    AIOrchestrationResponse,
    AIProgressChange,
    AIProgressSyncRequest,
    AIProgressSyncResponse,
    AIRagHit,
    AIRagQuery,
    AIRagResponse,
    AIRepoIndexResponse,
    AIWeeklyBrief,
)
from ..schemas.api import ActivityWrite
from . import activity_writes, ai_agent, ai_workspace, queries

_ALLOWED_ROOTS = ("backend", "frontend", "tests", "docs", ".github")
_ALLOWED_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".md", ".sql", ".json", ".yml", ".yaml", ".css"}
_SKIP_PARTS = {"node_modules", ".git", "dist", "build", ".venv", "__pycache__", "coverage"}
_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_-]{1,}|[0-9]{2,}")
_GITHUB_PR_RE = re.compile(r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)")
_BRANCH_RE = re.compile(r"^[A-Za-z0-9._/-]{1,120}$")
_RATE_BUCKETS: dict[str, deque[float]] = defaultdict(deque)


def _owned_project(project_id: str | None, user_id: str):
    return ai_workspace._project(project_id, user_id)  # noqa: SLF001


def guard_prompt(user_id: str, content: str) -> None:
    """Apply cheap abuse, injection, and request-rate controls before provider calls."""
    lowered = content.lower()
    blocked = (
        "ignore previous instructions",
        "reveal the system prompt",
        "print your system prompt",
        "show me hidden instructions",
        "exfiltrate secret",
        "dump environment variables",
    )
    if any(marker in lowered for marker in blocked):
        raise ValueError("The request contains a prompt-injection or secret-exfiltration pattern.")
    limit = max(1, int(os.getenv("AI_REQUESTS_PER_MINUTE", "20")))
    now = time.time()
    bucket = _RATE_BUCKETS[user_id]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= limit:
        raise ValueError("AI request rate limit exceeded. Try again shortly.")
    bucket.append(now)


def _repo_files() -> list[Path]:
    files: list[Path] = []
    max_bytes = max(16_384, int(os.getenv("AI_RAG_MAX_FILE_BYTES", "262144")))
    for root_name in _ALLOWED_ROOTS:
        root = REPOSITORY_ROOT / root_name
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in _ALLOWED_SUFFIXES:
                continue
            if any(part in _SKIP_PARTS for part in path.parts):
                continue
            try:
                if path.stat().st_size > max_bytes:
                    continue
            except OSError:
                continue
            files.append(path)
    return sorted(files)


def _chunks(text: str, size: int = 1600, overlap: int = 240) -> list[str]:
    cleaned = text.replace("\x00", "").strip()
    if not cleaned:
        return []
    result: list[str] = []
    start = 0
    while start < len(cleaned):
        end = min(len(cleaned), start + size)
        result.append(cleaned[start:end])
        if end == len(cleaned):
            break
        start = max(start + 1, end - overlap)
    return result


def index_repository(project_id: str | None, user_id: str) -> AIRepoIndexResponse:
    _owned_project(project_id, user_id)
    files = _repo_files()
    rows: list[tuple[str, int, str, str]] = []
    skipped = 0
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            skipped += 1
            continue
        rel = str(path.relative_to(REPOSITORY_ROOT))
        for index, chunk in enumerate(_chunks(text)):
            digest = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
            rows.append((rel, index, chunk, digest))
    with connect() as connection, connection:
        if project_id is None:
            connection.execute(
                "DELETE FROM ai_repo_chunks WHERE user_id = ? AND project_id IS NULL", (user_id,)
            )
        else:
            connection.execute(
                "DELETE FROM ai_repo_chunks WHERE user_id = ? AND project_id = ?",
                (user_id, project_id),
            )
        connection.executemany(
            """
            INSERT INTO ai_repo_chunks
              (user_id, project_id, path, chunk_index, content, content_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [(user_id, project_id, *row) for row in rows],
        )
    return AIRepoIndexResponse(
        projectId=project_id,
        filesIndexed=len(files) - skipped,
        chunksIndexed=len(rows),
        skippedFiles=skipped,
    )


def _tokens(value: str) -> set[str]:
    return {match.group(0).lower() for match in _TOKEN_RE.finditer(value)}


def query_repository(project_id: str | None, payload: AIRagQuery, user_id: str) -> AIRagResponse:
    _owned_project(project_id, user_id)
    with connect() as connection:
        if project_id is None:
            rows = connection.execute(
                """
                SELECT path, chunk_index, content FROM ai_repo_chunks
                WHERE user_id = ? AND project_id IS NULL
                """,
                (user_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                """
                SELECT path, chunk_index, content FROM ai_repo_chunks
                WHERE user_id = ? AND project_id = ?
                """,
                (user_id, project_id),
            ).fetchall()
    if not rows:
        index_repository(project_id, user_id)
        return query_repository(project_id, payload, user_id)
    query_tokens = _tokens(payload.query)
    phrase = payload.query.lower().strip()
    scored: list[tuple[float, object]] = []
    for row in rows:
        content = row["content"]
        content_tokens = _tokens(content)
        overlap = len(query_tokens & content_tokens)
        if overlap == 0 and phrase not in content.lower():
            continue
        score = overlap / max(1, len(query_tokens))
        if phrase and phrase in content.lower():
            score += 1.0
        if any(token in row["path"].lower() for token in query_tokens):
            score += 0.2
        scored.append((score, row))
    scored.sort(key=lambda item: (-item[0], item[1]["path"], item[1]["chunk_index"]))
    hits = [
        AIRagHit(
            path=row["path"],
            chunkIndex=row["chunk_index"],
            score=round(score, 4),
            excerpt=row["content"][:1200],
        )
        for score, row in scored[: payload.topK]
    ]
    return AIRagResponse(projectId=project_id, query=payload.query, hits=hits)


def _action_from_row(row) -> AIActionRecord:
    return AIActionRecord(
        id=row["id"],
        projectId=row["project_id"],
        kind=row["action_kind"],
        payload=json.loads(row["payload_json"]),
        status=row["status"],
        result=json.loads(row["result_json"]) if row["result_json"] else None,
        createdAt=row["created_at"],
        approvedAt=row["approved_at"],
        executedAt=row["executed_at"],
    )


def propose_action(payload: AIActionProposalRequest, user_id: str) -> AIActionRecord:
    _owned_project(payload.projectId, user_id)
    with connect() as connection, connection:
        cursor = connection.execute(
            """
            INSERT INTO ai_agent_actions (user_id, project_id, action_kind, payload_json, status)
            VALUES (?, ?, ?, ?, 'pending')
            """,
            (user_id, payload.projectId, payload.kind, json.dumps(payload.payload, sort_keys=True)),
        )
        row = connection.execute("SELECT * FROM ai_agent_actions WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _action_from_row(row)


def list_actions(project_id: str | None, user_id: str) -> list[AIActionRecord]:
    _owned_project(project_id, user_id)
    with connect() as connection:
        if project_id is None:
            rows = connection.execute(
                "SELECT * FROM ai_agent_actions WHERE user_id = ? AND project_id IS NULL ORDER BY id DESC",
                (user_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM ai_agent_actions WHERE user_id = ? AND project_id = ? ORDER BY id DESC",
                (user_id, project_id),
            ).fetchall()
    return [_action_from_row(row) for row in rows]


def approve_action(action_id: int, user_id: str) -> AIActionRecord:
    with connect() as connection, connection:
        cursor = connection.execute(
            """
            UPDATE ai_agent_actions SET status = 'approved', approved_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ? AND status = 'pending'
            """,
            (action_id, user_id),
        )
        if cursor.rowcount == 0:
            raise queries.NotFoundError(f"Unknown or non-pending AI action: {action_id}")
        row = connection.execute("SELECT * FROM ai_agent_actions WHERE id = ?", (action_id,)).fetchone()
    return _action_from_row(row)


def _activity(activity_id: str, user_id: str):
    item = next((item for item in queries.list_activities() if item.id == activity_id and item.userId == user_id), None)
    if item is None:
        raise queries.NotFoundError(f"Unknown activity: {activity_id}")
    return item


def _github_request(method: str, path: str, body: dict[str, object]) -> dict[str, object]:
    token = os.getenv("AI_GITHUB_TOKEN", "").strip()
    repository = os.getenv("AI_GITHUB_REPOSITORY", "").strip()
    if not token or not repository or "/" not in repository:
        raise RuntimeError("AI_GITHUB_TOKEN and AI_GITHUB_REPOSITORY are required for GitHub writes.")
    url = f"https://api.github.com/repos/{repository}{path}"
    req = request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "team-project-ai-agent",
        },
        method=method,
    )
    try:
        with request.urlopen(req, timeout=float(os.getenv("AI_GITHUB_TIMEOUT_SECONDS", "15"))) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:800]
        raise RuntimeError(f"GitHub action failed with HTTP {exc.code}: {detail}") from exc


def _execute_github(kind: str, payload: dict[str, object]) -> dict[str, object]:
    if kind == "github-issue":
        title = str(payload.get("title", "")).strip()
        if not title:
            raise ValueError("GitHub issue title is required.")
        result = _github_request("POST", "/issues", {"title": title, "body": str(payload.get("body", ""))})
        return {"number": result.get("number"), "url": result.get("html_url")}
    if kind == "github-pull-request":
        title = str(payload.get("title", "")).strip()
        head = str(payload.get("head", "")).strip()
        base = str(payload.get("base", "main")).strip()
        if not title or not _BRANCH_RE.fullmatch(head) or not _BRANCH_RE.fullmatch(base):
            raise ValueError("Valid PR title, head, and base are required.")
        result = _github_request(
            "POST",
            "/pulls",
            {"title": title, "head": head, "base": base, "body": str(payload.get("body", ""))},
        )
        return {"number": result.get("number"), "url": result.get("html_url")}
    if kind == "github-branch":
        branch = str(payload.get("branchName", "")).strip()
        base_ref = str(payload.get("baseRef", "main")).strip()
        if not _BRANCH_RE.fullmatch(branch) or not _BRANCH_RE.fullmatch(base_ref):
            raise ValueError("Valid branchName and baseRef are required.")
        repository = os.getenv("AI_GITHUB_REPOSITORY", "").strip()
        token = os.getenv("AI_GITHUB_TOKEN", "").strip()
        if not token or not repository:
            raise RuntimeError("AI_GITHUB_TOKEN and AI_GITHUB_REPOSITORY are required for GitHub writes.")
        base_url = f"https://api.github.com/repos/{repository}/git/ref/heads/{parse.quote(base_ref, safe='')}"
        req = request.Request(
            base_url,
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json", "User-Agent": "team-project-ai-agent"},
        )
        with request.urlopen(req, timeout=15) as response:
            ref_data = json.loads(response.read().decode("utf-8"))
        sha = ref_data["object"]["sha"]
        result = _github_request("POST", "/git/refs", {"ref": f"refs/heads/{branch}", "sha": sha})
        return {"ref": result.get("ref"), "sha": sha}
    raise ValueError(f"Unsupported GitHub action: {kind}")


def execute_action(action_id: int, user_id: str) -> AIActionRecord:
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM ai_agent_actions WHERE id = ? AND user_id = ?", (action_id, user_id)
        ).fetchone()
    if row is None or row["status"] != "approved":
        raise queries.NotFoundError(f"Unknown or unapproved AI action: {action_id}")
    project_id = row["project_id"]
    _owned_project(project_id, user_id)
    kind = row["action_kind"]
    payload = json.loads(row["payload_json"])
    result: dict[str, object]
    try:
        if kind == "create-task":
            created = activity_writes.create_activity(
                ActivityWrite(
                    userId=user_id,
                    date=str(payload.get("date", date.today().isoformat())),
                    title=str(payload.get("title", "AI generated task")),
                    status="planned",
                    projectId=project_id,
                )
            )
            result = created.model_dump()
        elif kind == "update-progress":
            item = _activity(str(payload.get("activityId", "")), user_id)
            status = str(payload.get("status", ""))
            updated = activity_writes.update_activity(
                item.id,
                ActivityWrite(
                    userId=item.userId,
                    date=item.date,
                    title=item.title,
                    status=status,
                    projectId=item.projectId,
                ),
            )
            result = updated.model_dump()
        elif kind == "record-decision":
            content = str(payload.get("content", "")).strip()
            if not content:
                raise ValueError("Decision content is required.")
            with connect() as connection, connection:
                cursor = connection.execute(
                    """
                    INSERT INTO ai_memory_events (user_id, project_id, event_type, content, source)
                    VALUES (?, ?, 'decision', ?, 'approved-action')
                    """,
                    (user_id, project_id, content),
                )
            result = {"memoryEventId": cursor.lastrowid, "content": content}
        elif kind == "link-github":
            activity_id = str(payload.get("activityId", ""))
            _activity(activity_id, user_id)
            link_kind = str(payload.get("kind", "commit"))
            reference = str(payload.get("reference", "")).strip()
            if link_kind not in {"branch", "commit", "pull-request", "issue"} or not reference:
                raise ValueError("Valid GitHub link kind and reference are required.")
            with connect() as connection, connection:
                cursor = connection.execute(
                    """
                    INSERT INTO ai_github_links (user_id, project_id, activity_id, kind, reference)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (user_id, project_id, activity_id, link_kind, reference),
                )
            result = {"linkId": cursor.lastrowid, "activityId": activity_id}
        elif kind.startswith("github-"):
            result = _execute_github(kind, payload)
        else:
            raise ValueError(f"Unsupported action kind: {kind}")
    except Exception as exc:
        with connect() as connection, connection:
            connection.execute(
                "UPDATE ai_agent_actions SET status = 'failed', result_json = ?, executed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (json.dumps({"error": type(exc).__name__, "detail": str(exc)[:1000]}), action_id),
            )
        raise
    with connect() as connection, connection:
        connection.execute(
            """
            UPDATE ai_agent_actions
            SET status = 'executed', result_json = ?, executed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (json.dumps(result), action_id),
        )
        final = connection.execute("SELECT * FROM ai_agent_actions WHERE id = ?", (action_id,)).fetchone()
    return _action_from_row(final)


def _pr_merged(reference: str) -> bool:
    match = _GITHUB_PR_RE.fullmatch(reference.strip())
    if not match:
        return False
    owner, repo, number = match.groups()
    req = request.Request(
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "team-project-ai-progress"},
    )
    try:
        with request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode("utf-8"))
        return bool(data.get("merged_at"))
    except (error.URLError, TimeoutError, ValueError):
        return False


def sync_progress(payload: AIProgressSyncRequest, user_id: str) -> AIProgressSyncResponse:
    _owned_project(payload.projectId, user_id)
    activities = [item for item in queries.list_activities() if item.userId == user_id]
    if payload.projectId is not None:
        activities = [item for item in activities if item.projectId == payload.projectId]
    by_id = {item.id: item for item in activities}
    with connect() as connection:
        if payload.projectId is None:
            rows = connection.execute(
                "SELECT activity_id, kind, reference FROM ai_github_links WHERE user_id = ? AND project_id IS NULL",
                (user_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT activity_id, kind, reference FROM ai_github_links WHERE user_id = ? AND project_id = ?",
                (user_id, payload.projectId),
            ).fetchall()
    evidence: dict[str, list[object]] = defaultdict(list)
    for row in rows:
        evidence[row["activity_id"]].append(row)
    changes: list[AIProgressChange] = []
    updated = []
    for activity_id, links in evidence.items():
        item = by_id.get(activity_id)
        if item is None or item.status == "completed":
            continue
        target = item.status
        reason = ""
        if any(link["kind"] == "pull-request" and _pr_merged(link["reference"]) for link in links):
            target = "completed"
            reason = "Linked pull request is merged."
        elif any(link["kind"] in {"branch", "commit", "pull-request"} for link in links):
            target = "in-progress"
            reason = "Linked GitHub implementation evidence exists."
        if target == item.status:
            continue
        applied = False
        if payload.apply:
            updated_item = activity_writes.update_activity(
                item.id,
                ActivityWrite(
                    userId=item.userId,
                    date=item.date,
                    title=item.title,
                    status=target,
                    projectId=item.projectId,
                ),
            )
            updated.append(updated_item)
            applied = True
        changes.append(
            AIProgressChange(
                activityId=item.id,
                fromStatus=item.status,
                toStatus=target,
                reason=reason,
                applied=applied,
            )
        )
    return AIProgressSyncResponse(projectId=payload.projectId, changes=changes, updatedActivities=updated)


def health_score(project_id: str | None, user_id: str) -> AIHealthScore:
    _owned_project(project_id, user_id)
    snapshot = ai_agent._snapshot(user_id, project_id)  # noqa: SLF001
    activities = [item for item in queries.list_activities() if item.userId == user_id]
    if project_id is not None:
        activities = [item for item in activities if item.projectId == project_id]
    completed = sum(item.status == "completed" for item in activities)
    total = max(1, len(activities))
    blocking = sum(item.severity == "error" for item in snapshot.findings)
    warnings = sum(item.severity == "warning" for item in snapshot.findings)
    delivery = max(0, min(100, int((completed / total) * 70 + snapshot.progressPercent * 0.3)))
    schedule = max(0, 100 - min(70, len(snapshot.overdueTasks) * 15))
    code = max(0, 100 - blocking * 25 - warnings * 8)
    security = max(0, 100 - blocking * 20 - warnings * 5)
    tests = 90 if not blocking else max(45, 90 - blocking * 15)
    with connect() as connection:
        if project_id is None:
            doc_count = connection.execute(
                "SELECT COUNT(*) FROM ai_repo_chunks WHERE user_id = ? AND project_id IS NULL AND path LIKE 'docs/%'",
                (user_id,),
            ).fetchone()[0]
        else:
            doc_count = connection.execute(
                "SELECT COUNT(*) FROM ai_repo_chunks WHERE user_id = ? AND project_id = ? AND path LIKE 'docs/%'",
                (user_id, project_id),
            ).fetchone()[0]
    documentation = min(100, 60 + min(40, doc_count * 2)) if doc_count else 55
    overall = round((delivery + code + security + tests + schedule + documentation) / 6)
    reasons: list[str] = []
    if snapshot.overdueTasks:
        reasons.append(f"{len(snapshot.overdueTasks)} overdue task(s) reduce schedule health.")
    if blocking:
        reasons.append(f"{blocking} blocking engineering finding(s) reduce code/security health.")
    if doc_count == 0:
        reasons.append("Repository index has no documentation chunks yet.")
    if not reasons:
        reasons.append("No critical tracked project-health issue is currently visible.")
    with connect() as connection, connection:
        connection.execute(
            """
            INSERT INTO ai_health_snapshots
              (user_id, project_id, overall_score, delivery_score, code_score, security_score,
               test_score, schedule_score, documentation_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, project_id, overall, delivery, code, security, tests, schedule, documentation),
        )
    return AIHealthScore(
        projectId=project_id,
        overall=overall,
        delivery=delivery,
        code=code,
        security=security,
        tests=tests,
        schedule=schedule,
        documentation=documentation,
        reasons=reasons,
    )


def weekly_brief(project_id: str | None, user_id: str) -> AIWeeklyBrief:
    _owned_project(project_id, user_id)
    snapshot = ai_agent._snapshot(user_id, project_id)  # noqa: SLF001
    health = health_score(project_id, user_id)
    activities = [item for item in queries.list_activities() if item.userId == user_id]
    if project_id is not None:
        activities = [item for item in activities if item.projectId == project_id]
    completed = sum(item.status == "completed" for item in activities)
    in_progress = sum(item.status == "in-progress" for item in activities)
    risks = [item.title for item in snapshot.findings if item.severity != "info"][:8]
    if snapshot.overdueTasks:
        risks.insert(0, f"{len(snapshot.overdueTasks)} overdue task(s)")
    priorities = [item.title for item in ai_agent._suggested_tasks(  # noqa: SLF001
        type("Thread", (), {"projectId": project_id})(), snapshot
    )[:6]]
    return AIWeeklyBrief(
        projectId=project_id,
        headline=f"Weekly health {health.overall}/100 with {snapshot.progressPercent}% tracked progress.",
        progressPercent=snapshot.progressPercent,
        healthScore=health.overall,
        completedTasks=completed,
        inProgressTasks=in_progress,
        overdueTasks=len(snapshot.overdueTasks),
        githubSignals=len(snapshot.githubSignals),
        risks=risks,
        nextWeek=priorities,
    )


def debug_logs(project_id: str | None, logs: str, user_id: str) -> AIDebugResponse:
    _owned_project(project_id, user_id)
    query = " ".join(sorted(_tokens(logs))[:40]) or logs[:400]
    hits = query_repository(project_id, AIRagQuery(query=query, topK=8), user_id).hits
    lowered = logs.lower()
    recommendations: list[str] = []
    if "traceback" in lowered or "exception" in lowered:
        recommendations.append("Start from the first application-owned frame in the traceback, not the final wrapper error.")
    if "timeout" in lowered:
        recommendations.append("Check network/provider timeouts and add bounded retry only for idempotent operations.")
    if "assert" in lowered or "failed" in lowered:
        recommendations.append("Reproduce the smallest failing test before changing implementation code.")
    if "401" in lowered or "403" in lowered:
        recommendations.append("Verify authentication, CSRF, and project ownership before debugging business logic.")
    if not recommendations:
        recommendations.append("Compare the highest-ranked repository chunks with the earliest concrete error in the logs.")
    return AIDebugResponse(
        projectId=project_id,
        summary=f"Retrieved {len(hits)} likely code context chunk(s) from the repository index.",
        suspectedFiles=hits,
        recommendations=recommendations,
    )


def search_memory(project_id: str | None, query: str, user_id: str) -> AIMemorySearchResponse:
    _owned_project(project_id, user_id)
    q_tokens = _tokens(query)
    matches: list[tuple[int, str]] = []
    with connect() as connection:
        if project_id is None:
            memory_rows = connection.execute(
                "SELECT memory_key, memory_value FROM ai_project_memory WHERE user_id = ? AND project_id IS NULL",
                (user_id,),
            ).fetchall()
            event_rows = connection.execute(
                "SELECT event_type, content, created_at FROM ai_memory_events WHERE user_id = ? AND project_id IS NULL",
                (user_id,),
            ).fetchall()
        else:
            memory_rows = connection.execute(
                "SELECT memory_key, memory_value FROM ai_project_memory WHERE user_id = ? AND project_id = ?",
                (user_id, project_id),
            ).fetchall()
            event_rows = connection.execute(
                "SELECT event_type, content, created_at FROM ai_memory_events WHERE user_id = ? AND project_id = ?",
                (user_id, project_id),
            ).fetchall()
    for row in memory_rows:
        text = f"{row['memory_key']}: {row['memory_value']}"
        score = len(q_tokens & _tokens(text))
        if score:
            matches.append((score, text))
    for row in event_rows:
        text = f"{row['created_at']} {row['event_type']}: {row['content']}"
        score = len(q_tokens & _tokens(text))
        if score:
            matches.append((score, text))
    matches.sort(key=lambda item: -item[0])
    return AIMemorySearchResponse(projectId=project_id, query=query, matches=[text for _, text in matches[:20]])


def orchestrate(project_id: str | None, user_id: str) -> AIOrchestrationResponse:
    _owned_project(project_id, user_id)
    review = ai_agent.multi_agent_review(project_id, user_id)
    health = health_score(project_id, user_id)
    consensus: list[str] = []
    next_actions: list[str] = []
    warning_titles: dict[str, int] = defaultdict(int)
    for result in review.results:
        consensus.append(f"{result.specialist}: {result.summary}")
        for finding in result.findings:
            if finding.severity != "info":
                warning_titles[finding.title] += 1
        next_actions.extend(task.title for task in result.suggestedTasks[:2])
    disagreements = [
        f"Specialists differ on priority for '{title}' because it appears in only one specialist pass."
        for title, count in warning_titles.items()
        if count == 1
    ][:8]
    dedup_actions = list(dict.fromkeys(next_actions))[:10]
    return AIOrchestrationResponse(
        projectId=project_id,
        executiveSummary=f"Seven specialists coordinated against shared project state. Current health is {health.overall}/100.",
        consensus=consensus[:10],
        disagreements=disagreements,
        nextActions=dedup_actions,
    )


def refresh_notifications(project_id: str | None, user_id: str) -> list[AINotification]:
    _owned_project(project_id, user_id)
    snapshot = ai_agent._snapshot(user_id, project_id)  # noqa: SLF001
    health = health_score(project_id, user_id)
    candidates: list[tuple[str, str, str, str]] = []
    if snapshot.overdueTasks:
        candidates.append(("overdue", "warning", "Overdue work detected", f"{len(snapshot.overdueTasks)} task(s) are overdue."))
    for finding in snapshot.findings:
        if finding.severity in {"warning", "error"}:
            candidates.append((f"finding:{finding.title}", finding.severity, finding.title, finding.detail))
    if health.overall < 70:
        candidates.append(("health-low", "warning", "Project health needs attention", f"Overall health is {health.overall}/100."))
    with connect() as connection, connection:
        for fingerprint, severity, title, detail in candidates:
            connection.execute(
                """
                INSERT OR IGNORE INTO ai_notifications
                  (user_id, project_id, fingerprint, severity, title, detail)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, project_id, fingerprint, severity, title, detail),
            )
    return list_notifications(project_id, user_id)


def list_notifications(project_id: str | None, user_id: str) -> list[AINotification]:
    _owned_project(project_id, user_id)
    with connect() as connection:
        if project_id is None:
            rows = connection.execute(
                "SELECT * FROM ai_notifications WHERE user_id = ? AND project_id IS NULL ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM ai_notifications WHERE user_id = ? AND project_id = ? ORDER BY created_at DESC",
                (user_id, project_id),
            ).fetchall()
    return [
        AINotification(
            id=row["id"],
            projectId=row["project_id"],
            severity=row["severity"],
            title=row["title"],
            detail=row["detail"],
            readAt=row["read_at"],
            createdAt=row["created_at"],
        )
        for row in rows
    ]
