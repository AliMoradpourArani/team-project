# ForgeFlow AI

A local-first university team platform that combines project/activity tracking, professor review and submission workflows, GitHub intelligence, and a governed AI project copilot.

The application is one shared workspace, not one duplicated website per student. Identity, ownership, tracked data, project manifests, and server-side authorization drive the experience.

## Current status

| Area | Status | Capabilities |
| --- | --- | --- |
| Foundation | ✅ Complete | FastAPI, React/Vite/TypeScript, SQLite migrations, reproducible setup |
| Activities | ✅ Complete | Activity CRUD, calendar, timeline, dashboards, Git-tracked source writes |
| Auth & roles | ✅ Complete | Student/professor sessions, Argon2, CSRF, ownership isolation |
| Engineering quality | ✅ Complete | pytest, Vitest, Playwright, Ruff, ESLint, Prettier, CodeQL, dependency audits |
| GitHub intelligence | ✅ Complete | Repository status, commits/PR metrics, contribution timeline, activity evidence links |
| Project integration | ✅ Complete | Generic project pages, manifests, onboarding gates, health checks, README preview |
| Project demos | ✅ Complete | Reviewed CLI execution, sandboxed static preview, validated OpenAPI preview |
| Professor review | ✅ Complete | Review queue, fixed 100-point rubric, written feedback, student read-only results |
| Submission & release | ✅ Complete | Immutable versioned submissions, SHA-256 snapshots, preflight, frozen release candidates |
| AI copilot | ✅ Complete | Persistent chat, snapshots, replanning, task generation, project memory |
| Repo intelligence | ✅ Complete | Bounded repository indexing and lexical RAG query |
| AI engineering | ✅ Complete | Diff-aware code review, log-grounded debugging, health scoring |
| Progress automation | ✅ Complete | GitHub-evidence progress inference with preview/apply modes |
| Governed actions | ✅ Complete | `propose -> approve -> execute`, task/memory/link actions, optional GitHub branch/issue/PR writes |
| Multi-agent intelligence | ✅ Complete | Seven specialist roles with provider-backed orchestration and deterministic fallback |
| Briefs & notifications | ✅ Complete | Daily/weekly project intelligence, persistent risk notifications, recurring maintenance |
| Production hardening | ✅ Complete | Prompt-injection guard, rate limits, bounded payloads, timeouts, secret isolation, audit records |

## What students can do

A linked student can:

- view their dashboard, activities, calendar, timeline, and projects,
- create/edit/complete/delete their own activities,
- inspect project integration/onboarding/health and documentation,
- preview or run reviewed project demos according to the typed runner contract,
- read professor review/score/feedback for their own project,
- create immutable project submissions when eligible,
- use persistent AI project chat and project snapshots,
- preview or apply AI-generated replans/tasks,
- store/search project memory and decisions,
- index/query the repository for relevant source context,
- run diff-aware AI code review and log-grounded debugging,
- view project health and daily/weekly intelligence,
- preview GitHub-evidence progress changes and explicitly apply them,
- propose, approve, and execute allowlisted AI actions,
- view AI notifications and multi-agent recommendations.

Students cannot access another student's protected project/activity/AI state by changing URLs or request parameters.

## What the professor can do

The professor can:

- view team/member progress and recent activity,
- inspect all member projects and integration health,
- view GitHub contribution signals,
- preview typed project demos and run reviewed executable demos when enabled,
- manage project review status, rubric scoring, and written feedback,
- control the submission window,
- inspect immutable submission history,
- run final-delivery preflight,
- freeze a release candidate only after blocking gates pass.

Professor writes remain limited to professor-owned runtime evaluation/submission/release controls. Shared student source data stays protected.

## AI platform

The in-app AI layer is intentionally governed rather than fully autonomous.

### Persistent project copilot

- project-scoped threads and messages,
- provider-backed chat when `AI_API_KEY` is configured,
- deterministic local fallback when no provider is configured,
- project snapshots, overdue tasks, GitHub signals, diagnostics, and memory context,
- task replanning with preview-by-default behavior.

### Repository RAG

```text
POST /api/ai/repo/index
POST /api/ai/repo/query
```

The current retrieval mode is explicitly `lexical-rag`. It indexes bounded UTF-8 code/docs under allowlisted repository roots and stores chunks only in runtime SQLite.

### Code review and debugging

```text
POST /api/ai/code-review
POST /api/ai/debug
```

These endpoints analyze supplied diffs/logs and ground findings in project/repository context.

### Health, briefs, and orchestration

```text
GET /api/ai/health
GET /api/ai/brief
GET /api/ai/weekly-brief
GET /api/ai/multi-agent-review
GET /api/ai/orchestrate
```

The orchestrator uses seven specialist roles: planner, project manager, code reviewer, debugger, progress tracker, GitHub agent, and documentation agent.

### Governed actions

```text
POST /api/ai/actions
POST /api/ai/actions/{id}/approve
POST /api/ai/actions/{id}/execute
```

Supported action categories include task creation, progress updates, decision recording, GitHub evidence linking, and optional GitHub branch/issue/pull-request creation.

No external side effect occurs just because the model suggests it. The action must be proposed, explicitly approved, and then executed through an allowlisted server handler.

### Progress intelligence

```text
POST /api/ai/progress/sync
```

Linked branch/commit/PR evidence can infer `in-progress`; a verifiably merged linked PR can infer `completed`. `apply=false` previews changes. Applied changes use the authoritative Git-tracked activity write path.

## Architecture

```text
                         React / Vite / TypeScript
                                   │
                                   ▼
                              FastAPI API
                                   │
               ┌───────────────────┼───────────────────┐
               │                   │                   │
               ▼                   ▼                   ▼
      Git-tracked JSON         SQLite runtime      GitHub / AI provider
      shared authority       private + AI state     external services
               │                   │                   │
               │                   ├─ auth/sessions    ├─ read intelligence
               │                   ├─ reviews          ├─ provider responses
               │                   ├─ submissions      └─ approved GitHub writes
               │                   ├─ AI threads
               │                   ├─ memory/RAG
               │                   └─ actions/audit
               │
               └─ activities/projects remain shared source of truth
```

Core stack:

- **Frontend:** React + Vite + TypeScript
- **Backend:** FastAPI + Pydantic
- **Database:** SQLite with append-only ordered SQL migrations
- **Shared source:** Git-tracked JSON under `data/`
- **Authentication:** Argon2 + server-side sessions + CSRF
- **AI:** OpenAI-compatible provider interface with local fallback
- **Repository intelligence:** bounded lexical RAG
- **Testing:** pytest, Vitest, Playwright
- **Quality/security:** Ruff, ESLint, Prettier, TypeScript, dependency audits, CodeQL

See [Architecture](docs/architecture.md) and [AI Autonomy Platform](docs/ai-autonomy-platform.md).

## Source of truth

Shared data remains Git-visible:

```text
data/
├── users/<user_id>.json
├── activities/<user_id>/<date>.json
└── projects/<project_id>.json
```

SQLite stores derived/private/runtime state such as authentication, project-run history, professor reviews, submissions/releases, AI threads/messages, memory, RAG chunks, governed action records, and notifications.

AI automation must not bypass the source-authority contract. Applied task changes go through the same activity write/reconciliation service as normal user edits.

## Quick start

Prerequisites: Git, Python 3.11+, Node.js 20+, npm.

```bash
git clone https://github.com/HoosseinRahimi/ForgeFlow-AI-Core.git
cd ForgeFlow-AI-Core
make setup
make db-init
make db-sync
make auth-bootstrap
```

Run backend:

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload
```

Run frontend:

```bash
npm run dev --prefix frontend
```

Open:

- App: <http://localhost:5173>
- API: <http://localhost:8000>
- FastAPI docs: <http://localhost:8000/docs>

## Docker

```bash
docker compose up -d --build
docker compose exec backend python -m backend.auth.bootstrap
```

Docker mounts:

```text
./data        -> /app/data       read/write shared tracked state
./projects    -> /app/projects   read-only reviewed project source
team-runtime  -> /app/runtime    private SQLite/runtime state
```

Copy `.env.example` to a local environment file or export variables through your deployment secret/config system. Never commit real provider/GitHub credentials.

## Important runtime configuration

### Read-only GitHub intelligence

```text
GITHUB_INTEGRATION_ENABLED=true
GITHUB_REPOSITORY=HoosseinRahimi/ForgeFlow-AI-Core
GITHUB_CACHE_TTL_SECONDS=60
GITHUB_API_TIMEOUT_SECONDS=5
```

`GITHUB_TOKEN` is optional and should be read-only.

### AI provider

```text
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-5-mini
AI_TIMEOUT_SECONDS=20
AI_REQUESTS_PER_MINUTE=20
AI_RAG_MAX_FILE_BYTES=262144
```

`AI_API_KEY` is server-only and optional. Without it, deterministic local capabilities remain available.

### Recurring AI maintenance

```text
AI_AUTOMATION_ENABLED=true
AI_AUTOMATION_INTERVAL_SECONDS=3600
AI_AUTOMATION_APPLY_PROGRESS=false
```

Automatic progress mutation is off by default.

### Governed GitHub writes

```text
AI_GITHUB_REPOSITORY=HoosseinRahimi/ForgeFlow-AI-Core
AI_GITHUB_TIMEOUT_SECONDS=15
```

`AI_GITHUB_TOKEN` is a separate server-only credential and is required only for approved AI GitHub branch/issue/PR actions.

See `.env.example` for the complete safe configuration surface.

## Project integration and demos

A member project has:

1. authoritative metadata in `data/projects/<project_id>.json`,
2. reviewed source under `projects/<owner>/<project-directory>/`.

Required source layout:

```text
projects/<owner>/<project-directory>/
├── project.json
├── README.md
└── <typed-entry-point>
```

Supported typed demo contracts:

| Project type | Runner | Demo mode |
| --- | --- | --- |
| `cli` | `python-script-v1` | controlled execution |
| `static-web` | `static-site-v1` | sandboxed preview |
| `api` | `openapi-json-v1` | validated preview |

The Python runner is disabled by default and is not a sandbox for hostile code.

## Submission and final delivery

The final flow remains:

```text
integrate -> freeze final source -> professor approves after freeze -> preflight -> release candidate
```

Useful commands:

```bash
make project-check PROJECT_ID=<project_id>
make delivery-preflight-report
make delivery-preflight
```

## Testing and quality

```bash
make test
```

CI covers backend lint/tests/coverage, fresh DB initialization, onboarding/preflight contracts, frontend lint/format/types/unit/build, Playwright E2E, dependency audits, CodeQL, and optional AI PR review.

A green `AI Review` workflow does not necessarily mean a provider reviewed the diff if the Actions secret is not configured; the workflow intentionally succeeds with review skipped in that case.

## Git workflow

```text
main
  └── feature/fix/docs branch
          ↓
         PR
          ↓
    CI + security + review
          ↓
       squash merge
          ↓
         main
```

Keep normal development off `main`, resolve conflicts on the feature branch, and never force-push `main`.

## Documentation

Start with the [documentation index](docs/README.md).

Key documents:

- [Architecture](docs/architecture.md)
- [AI Autonomy Platform](docs/ai-autonomy-platform.md)
- [Authentication](docs/authentication.md)
- [GitHub Integration](docs/github-integration.md)
- [Database Rules](docs/database-rules.md)
- [Engineering Quality](docs/engineering-quality.md)
- [Member Project Onboarding](docs/member-project-onboarding.md)
- [Project Review & Evaluation](docs/project-review-evaluation.md)
- [Submission & Release](docs/submission-release.md)
- [Final Delivery Preflight](docs/final-delivery-preflight.md)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Changelog](CHANGELOG.md)

## API conventions

- routes use `/api/`,
- request/response contracts are typed,
- authorization is server-side,
- Git-tracked JSON stays authoritative for shared project/task state,
- credentials/sessions/provider tokens/AI runtime state stay outside Git,
- external integrations use trusted server configuration and bounded permissions,
- durable AI side effects require explicit governed control paths,
- arbitrary shell execution through project manifests is forbidden.
