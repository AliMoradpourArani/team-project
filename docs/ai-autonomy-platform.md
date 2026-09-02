# AI Autonomy Platform

This layer extends the project copilot into a governed project operating system. It is designed around one rule: model output may propose work, but durable or external mutations require an explicit, authenticated control path.

## Capabilities

### Repository RAG

`POST /api/ai/repo/index` indexes bounded UTF-8 source/documentation files from `backend/`, `frontend/`, `tests/`, `docs/`, and `.github/` into project-scoped chunks. `POST /api/ai/repo/query` retrieves ranked context for debugging and review. The local retrieval mode is intentionally reported as `lexical-rag`; it does not pretend to be an embedding model.

### Diff-aware code review and debugging

`POST /api/ai/code-review` reviews supplied diffs for project invariants, likely secret exposure, dangerous execution patterns, destructive migration changes, and missing visible tests, then grounds the result with repository retrieval. `POST /api/ai/debug` maps error logs to likely repository chunks and deterministic next steps.

### Evidence-backed progress

`POST /api/ai/progress/sync` derives task movement from linked GitHub evidence. Branches, commits, and open PR evidence can move planned work to `in-progress`; a verifiably merged public GitHub PR can move work to `completed`. `apply=false` previews changes. `apply=true` writes through the existing authoritative activity-write service, preserving the Git-tracked JSON source of truth.

### Governed action engine

AI actions follow three states before side effects:

1. propose with `POST /api/ai/actions`
2. approve with `POST /api/ai/actions/{id}/approve`
3. execute with `POST /api/ai/actions/{id}/execute`

Supported actions include task creation, progress updates, decision memory, GitHub evidence links, GitHub branch creation, issue creation, and pull-request creation. Every proposal and execution result is persisted in `ai_agent_actions`.

GitHub writes require both server-side variables:

- `AI_GITHUB_TOKEN`
- `AI_GITHUB_REPOSITORY=owner/repo`

No browser-provided token or model-generated credential is accepted.

### Memory and intelligence

Structured memory remains available through `/api/ai/memory`. Approved decisions are appended to `ai_memory_events`; `/api/ai/memory/search` retrieves both structured memory and event history. Daily and weekly briefs, multi-agent orchestration, and project health scoring combine tracked work, diagnostics, GitHub signals, documentation index state, and overdue work.

### Multi-agent orchestration

Seven specialist roles share the same authorized project snapshot: planner, project manager, code reviewer, debugger, progress tracker, GitHub agent, and documentation agent. When `AI_API_KEY` is configured, `/api/ai/orchestrate` runs provider-backed specialist assessments. Without a provider, the endpoint uses deterministic specialist fallbacks and explicitly reports that mode.

### Notifications and recurring automation

Project-risk notifications are persisted in `ai_notifications`. A lightweight FastAPI maintenance loop refreshes health and notifications while the application is running.

Configuration:

- `AI_AUTOMATION_ENABLED=true` enables the loop.
- `AI_AUTOMATION_INTERVAL_SECONDS=3600` controls cadence; minimum is 300 seconds.
- `AI_AUTOMATION_APPLY_PROGRESS=false` keeps automatic task mutation off by default. Set it to `true` only when evidence-backed automatic progress updates are desired.

## Production hardening

The platform includes:

- authenticated student/project scope checks before retrieval or mutation
- CSRF protection for durable mutations
- explicit proposal/approval/execution boundaries
- provider and GitHub HTTP timeouts
- server-only secrets
- prompt-injection / secret-exfiltration pattern rejection before chat provider calls
- per-user AI request-rate limiting through `AI_REQUESTS_PER_MINUTE`
- bounded repository roots, file types, file sizes, chunk sizes, query sizes, and diff/log payload sizes
- local deterministic fallbacks when the model provider is unavailable
- append-only database migration history
- health snapshots and action execution records for auditability

The repository continues to treat Git-tracked JSON under `data/` as authoritative shared task/project state. The autonomy layer must not bypass that contract.

## Recommended deployment settings

```bash
AI_API_KEY=...
AI_MODEL=gpt-5-mini
AI_BASE_URL=https://api.openai.com/v1
AI_TIMEOUT_SECONDS=20
AI_REQUESTS_PER_MINUTE=20
AI_RAG_MAX_FILE_BYTES=262144
AI_AUTOMATION_ENABLED=true
AI_AUTOMATION_INTERVAL_SECONDS=3600
AI_AUTOMATION_APPLY_PROGRESS=false
AI_GITHUB_TOKEN=...
AI_GITHUB_REPOSITORY=owner/repo
AI_GITHUB_TIMEOUT_SECONDS=15
```

Do not commit any of these secret values to the repository.
