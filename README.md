# Team Project

A local-first university team platform for recording daily work, presenting individual progress, integrating reviewed member projects, and giving the professor a clear team view.

The application is one shared platform, not one duplicated website per student. Authentication, activities, calendar, timeline, dashboards, GitHub integration, and project execution are implemented once and become user-specific through data and authorization.

## Current status

| Phase | Status | What it adds |
| --- | --- | --- |
| Phase 1 | ✅ Complete | FastAPI/React/SQLite foundation, migrations, reproducible setup, Git workflow |
| Phase 2 | ✅ Complete | Activity CRUD, calendar, timeline, personal dashboard, Git-tracked activity writes |
| Phase 2.5 | ✅ Complete | E2E, coverage gates, security scanning, CODEOWNERS, Dependabot, observability, optional AI PR review |
| Phase 3 | ✅ Complete | Local authentication, student/professor authorization, CSRF protection, professor dashboard |
| Phase 4 | ✅ Complete | Read-only GitHub integration, repository status, commit/PR metrics, contribution timeline |
| Phase 5 | ✅ Complete | Validated Project Integration / Runner for reviewed member projects |

## What the platform does

### Student experience

Each student signs in to a protected personal workspace and can:

- view their own profile and dashboard
- create, edit, complete, and delete daily activities
- browse work through a calendar
- review activity history in a timeline
- see their assigned/integrated projects
- inspect project integration state (`ready`, `not-integrated`, `invalid`)
- run their own reviewed project demo when the local runner is explicitly enabled
- keep shared activity/project metadata Git-visible for review and version history

A student cannot access another student's protected data or runner endpoint by changing a URL or API parameter.

### Professor experience

The professor gets a team view with:

- team-wide progress and completion totals
- recent activities across members
- member drill-down dashboards
- project summaries and integration state
- GitHub repository status
- per-member recent commit and pull-request metrics
- a combined GitHub contribution timeline
- controlled execution of reviewed project demos when the local runner is enabled

The professor remains read-only for shared student data. Invoking a reviewed demo returns runtime output but does not intentionally write project metadata or activities.

GitHub metrics are repository signals, not productivity scores.

## Architecture

The project uses a **modular monolith**.

```text
                         Team Project
                              │
              ┌───────────────┴───────────────┐
              │                               │
          React/Vite                       FastAPI
          TypeScript                       Backend
              │                               │
              └────────────── API ────────────┘
                                              │
                 ┌────────────────────────────┼──────────────────────────┐
                 │                            │                          │
          Git-tracked JSON                  SQLite                   GitHub API
          shared source data              runtime DB               read-only data
                 │
                 └── projects/<owner>/<project>/
                             │
                             └── validated allowlisted runner (opt-in)
```

Core technology:

- **Frontend:** React + Vite + TypeScript
- **Backend:** FastAPI + Pydantic
- **Database:** SQLite with ordered SQL migrations
- **Shared source data:** Git-tracked JSON under `data/`
- **Authentication:** Argon2 passwords + server-side sessions + CSRF
- **GitHub integration:** read-only API client with short-lived cache
- **Project integration:** validated manifest + allowlisted runner contract
- **Testing:** pytest, Vitest, Playwright
- **Quality/security:** Ruff, ESLint, Prettier, TypeScript, dependency audits, CodeQL
- **Runtime:** native development or Docker Compose

Detailed docs:

- [Architecture](docs/architecture.md)
- [Authentication](docs/authentication.md)
- [GitHub integration](docs/github-integration.md)
- [Project contract](docs/project-contract.md)
- [Project runner](docs/project-runner.md)
- [Architecture decisions](docs/adr/)

## Source of truth

Shared project data is Git-visible:

```text
data/
├── users/<user_id>.json
├── activities/<user_id>/<date>.json
└── projects/<project_id>.json
```

These files are authoritative for users, activities, project metadata, and optional GitHub identity mappings. SQLite is the runtime representation and also stores private local authentication state.

```text
Git-tracked JSON
      │
      ▼
   db-sync
      │
      ▼
    SQLite
      │
      ▼
  FastAPI API
      │
      ▼
   React UI
```

Passwords, password hashes, sessions, API tokens, and other secrets are never stored in Git-tracked user JSON.

## Repository structure

```text
team-project/
├── frontend/                  # React/Vite/TypeScript UI
├── backend/
│   ├── auth/                  # Local account bootstrap
│   ├── app/                   # FastAPI routes/dependencies/observability
│   ├── schemas/               # API/source/auth/GitHub/runner contracts
│   ├── services/              # Business logic and integrations
│   └── database/              # SQLite migrations/init/sync
├── data/                      # Authoritative shared data
├── projects/<owner>/<name>/   # Reviewed member project source + project.json
├── e2e/                       # Playwright flows
├── tests/                     # Backend tests
├── docs/
├── .github/
├── CHANGELOG.md
├── SECURITY.md
├── docker-compose.yml
└── Makefile
```

## Prerequisites

Native development:

- Git
- Python 3.11+ (3.12+ recommended)
- Node.js 20+
- npm

Docker is optional.

## Quick start: native

```bash
git clone https://github.com/HoosseinRahimi/team-project.git
cd team-project
make setup
make db-init
make db-sync
make auth-bootstrap
```

Run `make auth-bootstrap` once for each student account and once for the professor account. A student account must link to an existing tracked `user_id`.

Start the backend:

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload
```

Start the frontend in another terminal:

```bash
npm run dev --prefix frontend
```

Open:

- Application: <http://localhost:5173>
- API: <http://localhost:8000>
- FastAPI docs: <http://localhost:8000/docs>

## Quick start: Docker

```bash
docker compose up -d --build
docker compose exec backend python -m backend.auth.bootstrap
```

Then open <http://localhost:5173>.

Docker mounts:

```text
./data     -> /app/data       (read/write, Git-visible shared data)
./projects -> /app/projects   (read-only project source)
team-runtime -> /app/runtime  (private SQLite/auth runtime state)
```

Stop with:

```bash
docker compose down
```

Use `docker compose down -v` only when you intentionally want to delete local runtime database/authentication state.

## Authentication and authorization

### Student

- linked to exactly one tracked user
- reads only their own protected user/activity/project data
- modifies only their own activities
- can inspect only their visible project integrations
- can invoke the runner only for their own project
- cannot access professor endpoints

### Professor

- views all team members and project/activity summaries
- drills into member dashboards
- views GitHub contribution analytics
- can invoke reviewed project demos when execution is enabled
- does not receive normal write access to student activities/project metadata

Authentication endpoints:

```text
POST /api/auth/login
GET  /api/auth/me
POST /api/auth/logout
```

Professor endpoints:

```text
GET /api/professor/dashboard
GET /api/professor/github
```

Session cookies are HttpOnly and SameSite=Lax. Unsafe authenticated requests require `X-CSRF-Token`.

## Activities, calendar, and timeline

```text
GET    /api/activities
POST   /api/activities
PUT    /api/activities/{activity_id}
DELETE /api/activities/{activity_id}
```

Activity writes update authoritative Git-tracked JSON and then reconcile SQLite.

## GitHub integration

A user can declare an explicit mapping:

```json
{
  "id": "hossein",
  "display_name": "Hossein",
  "role": "Developer",
  "github_username": "HoosseinRahimi"
}
```

The application never guesses GitHub accounts from names/emails. Unlinked members stay explicit.

Default runtime configuration:

```text
GITHUB_INTEGRATION_ENABLED=true
GITHUB_REPOSITORY=HoosseinRahimi/team-project
GITHUB_CACHE_TTL_SECONDS=60
GITHUB_API_TIMEOUT_SECONDS=5
```

Public repositories work without a token at lower rate limits. For private access/higher limits, export a read-only `GITHUB_TOKEN` at runtime. Never commit it.

## Project Integration / Runner

Each executable member project has two linked pieces:

1. authoritative metadata under `data/projects/<project_id>.json`
2. source + validated manifest under `projects/<owner>/<project-directory>/project.json`

Example manifest:

```json
{
  "id": "team-foundation",
  "name": "Team Project Foundation",
  "owner_id": "hossein",
  "description": "Runnable demonstration for the shared team platform project.",
  "technology": ["python"],
  "project_type": "cli",
  "runner": "python-script-v1",
  "entry_point": "main.py",
  "repository_path": "projects/hossein/team-platform"
}
```

Phase 5 intentionally supports only:

```text
project_type = cli
runner       = python-script-v1
```

The backend derives argv itself and runs:

```text
<backend-python> -B <validated-entry-point>
```

It does **not** execute manifest fields such as `run`, `build`, `command`, or arbitrary shell text. Such extra fields are rejected.

Project endpoints:

```text
GET  /api/projects
GET  /api/projects/integrations
POST /api/projects/{project_id}/run
```

Execution is disabled by default:

```text
PROJECT_RUNNER_ENABLED=false
PROJECT_RUNNER_TIMEOUT_SECONDS=5
PROJECT_RUNNER_OUTPUT_LIMIT=16000
```

After the executable code has passed PR/CI/review, a local demo can opt in:

```bash
export PROJECT_RUNNER_ENABLED=true
```

or with Docker:

```bash
PROJECT_RUNNER_ENABLED=true docker compose up -d --build
```

### Important security boundary

The runner prevents manifest-driven shell execution, validates ownership/paths, rejects symlinked executable paths, uses `shell=False`, limits runtime/output returned to the UI, and mounts project source read-only in Docker.

It is **not a sandbox for hostile code**. Reviewed Python code can still use operating-system/network permissions available to the backend process. Do not enable the runner for untrusted submissions. A future untrusted-code feature would require a dedicated isolated execution service/container boundary.

See [docs/project-runner.md](docs/project-runner.md) and [ADR 0004](docs/adr/0004-controlled-project-runner.md).

## Database commands

```bash
make db-init
make db-sync
make db-reset
```

Merged SQL migrations are append-only. Do not rewrite a migration that has already landed on `main`.

## Testing and quality gates

```bash
make test
```

Individual checks:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check backend tests
npm run lint --prefix frontend
npm run format:check --prefix frontend
npm run type-check --prefix frontend
npm test --prefix frontend
npm run build --prefix frontend
```

CI covers:

- conflict-marker detection
- backend lint/tests/coverage + fresh DB sync
- frontend lint/Prettier/TypeScript/unit/build
- Playwright Chromium E2E
- Python/npm dependency audits
- CodeQL for Python and JavaScript/TypeScript

Executable project paths are CODEOWNERS-protected because any project code may become locally runnable after explicit enablement.

## Observability

```text
GET /api/health
GET /health
```

API responses include `X-Request-ID`, and request metadata is logged as structured JSON.

## Configuration

Use `.env.example` as the reference. Important values include:

```text
AUTH_COOKIE_NAME=team_session
AUTH_COOKIE_SECURE=false
AUTH_SESSION_HOURS=8
GITHUB_INTEGRATION_ENABLED=true
GITHUB_REPOSITORY=HoosseinRahimi/team-project
PROJECT_RUNNER_ENABLED=false
PROJECT_RUNNER_TIMEOUT_SECONDS=5
PROJECT_RUNNER_OUTPUT_LIMIT=16000
```

Set `AUTH_COOKIE_SECURE=true` when serving over HTTPS.

## Git workflow

`main` is the stable integration branch and should remain runnable for the professor.

```text
main
  └── feature/fix/docs branch
          ↓
        commits
          ↓
           PR
          ↓
      CI + review
          ↓
      squash merge
          ↓
         main
```

Branch names:

```text
feature/<name>
fix/<name>
docs/<name>
refactor/<name>
test/<name>
chore/<name>
```

Rules:

- no normal development directly on `main`
- resolve conflicts on feature branches
- no force-push to `main`
- prefer focused PRs + squash merge
- executable project code must pass normal review/CI before local runner enablement

Conventional Commit prefixes:

```text
feat: fix: docs: refactor: test: chore: ci: build:
```

## Project direction

```text
Shared Platform
├── Authentication
├── Activity System
├── Calendar
├── Timeline
├── Student Dashboard
├── Professor Dashboard
├── GitHub Integration
└── Project Integration / Runner
      ├── Member A specialized project
      ├── Member B specialized project
      └── Member C specialized project
```

Future runner expansion should add explicit, reviewed runner types rather than accepting arbitrary commands. If execution ever needs to accept untrusted code, it must move behind a stronger sandbox/isolation boundary.

## Documentation

- [Architecture](docs/architecture.md)
- [Authentication](docs/authentication.md)
- [GitHub integration](docs/github-integration.md)
- [Project contract](docs/project-contract.md)
- [Project runner](docs/project-runner.md)
- [Git workflow](docs/git-workflow.md)
- [Database rules](docs/database-rules.md)
- [Branch protection](docs/branch-protection.md)
- [Engineering quality](docs/engineering-quality.md)
- [Architecture decision records](docs/adr/)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Changelog](CHANGELOG.md)

## API conventions

- prefix application routes with `/api/`
- use typed Pydantic request/response contracts
- return structured errors
- unknown resources -> `404`
- malformed input -> `422`
- unauthenticated -> `401`
- forbidden -> `403`
- never trust a frontend-provided user id as authorization proof
- keep Git-tracked JSON authoritative for shared team data
- keep credentials/sessions/secrets in runtime-only state
- keep external integrations isolated/read-only where possible
- never introduce arbitrary shell execution through project manifests
