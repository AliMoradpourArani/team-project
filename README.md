# Team Project

A local-first university team platform for recording daily work, presenting individual progress, integrating student projects, and giving the professor a clear read-only view of the team.

The application is designed as one shared platform, not one duplicated website per student. Shared features such as authentication, activities, calendar, timeline, dashboards, and GitHub integration are implemented once and become user-specific through data and authorization.

## Current status

| Phase | Status | What it adds |
| --- | --- | --- |
| Phase 1 | ✅ Complete | FastAPI/React/SQLite foundation, migrations, reproducible setup, Git workflow |
| Phase 2 | ✅ Complete | Activity CRUD, calendar, timeline, personal dashboard, Git-tracked activity writes |
| Phase 2.5 | ✅ Complete | E2E testing, coverage gates, security scanning, CODEOWNERS, Dependabot, observability, optional AI PR review |
| Phase 3 | ✅ Complete | Local authentication, student/professor authorization, CSRF protection, professor dashboard |
| Phase 4 | ✅ Complete | Read-only GitHub integration, repository status, commit/PR metrics, contribution timeline |
| Project Runner | ⏳ Planned | Controlled execution/integration of each member's specialized project |

## What the platform does

### Student experience

Each student signs in to a protected personal workspace and can:

- view their own profile and dashboard
- create, edit, complete, and delete daily activities
- browse work through a calendar
- review activity history in a timeline
- see their assigned/integrated projects
- keep shared activity data Git-visible for review and version history

A student cannot access another student's protected data by changing a URL or API parameter.

### Professor experience

The professor gets a read-only team view with:

- team-wide progress and completion totals
- recent activities across members
- member drill-down dashboards
- project summaries
- GitHub repository status
- per-member recent commit and pull-request metrics
- a combined GitHub contribution timeline

GitHub metrics are treated as repository signals, not as a productivity score.

## Architecture

The project uses a **modular monolith**. There are no microservices.

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
                         ┌────────────────────┼────────────────────┐
                         │                    │                    │
                   Git-tracked JSON        SQLite              GitHub API
                   shared source data     runtime DB          read-only data
```

Core technology:

- **Frontend:** React + Vite + TypeScript
- **Backend:** FastAPI + Pydantic
- **Database:** SQLite with ordered SQL migrations
- **Shared source data:** Git-tracked JSON under `data/`
- **Authentication:** local accounts, Argon2 password hashing, server-side sessions
- **External integration:** read-only GitHub API client with short-lived cache
- **Testing:** pytest, Vitest, Playwright
- **Quality/security:** Ruff, ESLint, Prettier, TypeScript checks, dependency audits, CodeQL
- **Runtime:** native development or Docker Compose

Detailed architecture lives in [docs/architecture.md](docs/architecture.md), [docs/authentication.md](docs/authentication.md), [docs/github-integration.md](docs/github-integration.md), and [docs/adr/](docs/adr/).

## Data model and source of truth

Shared project data is intentionally Git-visible:

```text
data/
├── users/<user_id>.json
├── activities/<user_id>/<date>.json
└── projects/<project_id>.json
```

These JSON files are the authoritative shared source for:

- users
- activities
- projects
- optional GitHub username mappings

SQLite is a derived runtime representation for shared data and also stores private local authentication state.

```text
JSON source files
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

Passwords, password hashes, sessions, and secrets are **never** stored in Git-tracked user JSON.

## Repository structure

```text
team-project/
├── frontend/                 # React/Vite/TypeScript application
│   └── src/
├── backend/
│   ├── auth/                 # Local account bootstrap
│   ├── app/                  # FastAPI app, routes, auth dependencies, observability
│   ├── schemas/              # API/auth/source-data/GitHub contracts
│   ├── services/             # Business logic and integrations
│   └── database/
│       ├── migrations/       # Ordered SQL migrations
│       ├── init_db.py
│       ├── sync_data.py
│       └── source_files.py
├── data/                     # Authoritative Git-tracked shared data
├── e2e/                      # Playwright browser flows
├── projects/<owner>/<name>/  # Member projects and manifests
├── scripts/
├── docs/
├── tests/
├── .github/
├── CHANGELOG.md
├── SECURITY.md
├── docker-compose.yml
└── Makefile
```

## Prerequisites

For native development:

- Git
- Python 3.11+ (3.12+ recommended)
- Node.js 20+
- npm

Docker is optional.

## Quick start: native

Clone and bootstrap the project:

```bash
git clone https://github.com/HoosseinRahimi/team-project.git
cd team-project
make setup
```

Initialize/reconcile the database:

```bash
make db-init
make db-sync
```

Create local login accounts:

```bash
make auth-bootstrap
```

Run the bootstrap once for each student account and once for the professor account. A student account must link to an existing tracked `user_id` such as `hossein`, `ali`, or `reza`.

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
```

Create accounts inside the backend container:

```bash
docker compose exec backend python -m backend.auth.bootstrap
```

Then open <http://localhost:5173>.

Docker bind-mounts `./data:/app/data`, so shared activity changes remain visible to Git. Runtime SQLite/authentication state is stored separately in the `team-runtime` named volume.

Stop the stack with:

```bash
docker compose down
```

Use `docker compose down -v` only when you intentionally want to delete local runtime database/authentication state.

## Authentication and authorization

### Student

A student account:

- is linked to exactly one tracked user
- can read its own protected user/activity/project data
- can modify only its own activities
- cannot open professor endpoints
- cannot impersonate another member with a URL/API parameter

### Professor

The professor account:

- can view all team members
- can inspect team activity/project summaries
- can drill into member dashboards
- can view read-only GitHub contribution analytics
- is intentionally read-only for student work

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

Session cookies are HttpOnly and SameSite=Lax. Unsafe authenticated requests also require the CSRF token in `X-CSRF-Token`.

See [docs/authentication.md](docs/authentication.md).

## Activities, calendar, and timeline

Activities are shared source data with stable IDs and per-user ownership.

Protected activity endpoints include:

```text
GET    /api/activities
POST   /api/activities
PUT    /api/activities/{activity_id}
DELETE /api/activities/{activity_id}
```

Web/API writes update the authoritative activity JSON and reconcile the runtime database, keeping the normal academic workflow Git-visible:

```text
Student updates work
       │
       ▼
Git-tracked JSON
       │
       ▼
commit → PR → merge main
       │
       ▼
Professor git pull
       │
       ▼
make db-sync / application startup
       │
       ▼
Updated website data
```

## GitHub integration

Phase 4 adds a professor-only, read-only GitHub view.

A tracked user can optionally declare an explicit GitHub identity:

```json
{
  "id": "hossein",
  "display_name": "Hossein",
  "role": "Developer",
  "github_username": "HoosseinRahimi"
}
```

Then reconcile the data:

```bash
make db-sync
```

The application never guesses GitHub accounts from display names or email addresses. Members without a mapping remain visible as **not linked**.

The professor GitHub panel shows:

- repository/default-branch status
- open pull requests
- recent default-branch commits
- commit counts for linked members
- authored/merged/open pull-request counts
- latest contribution timestamp
- recent combined commit/PR timeline

Default configuration:

```text
GITHUB_INTEGRATION_ENABLED=true
GITHUB_REPOSITORY=HoosseinRahimi/team-project
GITHUB_CACHE_TTL_SECONDS=60
GITHUB_API_TIMEOUT_SECONDS=5
```

Public repositories can work without a token. To increase rate limits or access a private repository, provide a read-only token at runtime:

```bash
export GITHUB_TOKEN='...'
```

Never commit `GITHUB_TOKEN`.

If GitHub is unavailable or rate-limited, the core professor dashboard remains available and the GitHub panel degrades to an offline-safe state.

See [docs/github-integration.md](docs/github-integration.md).

## Database commands

```bash
make db-init        # Apply migrations and initialize the database
make db-sync        # Reconcile Git-tracked shared data into SQLite
make db-reset       # Delete the native local development database
```

Equivalent Python commands:

```bash
.venv/bin/python -m backend.database.init_db --seed
.venv/bin/python -m backend.database.sync_data
```

Merged migrations are append-only. Do not rewrite an already merged migration.

See [docs/database-rules.md](docs/database-rules.md).

## Testing and quality gates

Run the normal test suite:

```bash
make test
```

Useful individual checks:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check backend tests
npm run lint --prefix frontend
npm run format:check --prefix frontend
npm run type-check --prefix frontend
npm test --prefix frontend
npm run build --prefix frontend
```

CI currently covers:

- unresolved conflict-marker detection
- backend lint/tests/coverage
- fresh database initialization and synchronization
- frontend lint/Prettier/TypeScript/unit tests/build
- Playwright Chromium E2E flows
- Python dependency audit
- npm dependency audit
- CodeQL for Python and JavaScript/TypeScript

E2E tests disable external GitHub access so CI does not depend on GitHub API availability. GitHub aggregation is tested deterministically with fixtures/mocks.

## Observability

Public health checks:

```text
GET /api/health
GET /health
```

API responses include an `X-Request-ID` correlation header. Request metadata is logged as structured JSON to make local debugging and integration failures easier to trace.

## Configuration

Copy/use `.env.example` as the reference configuration.

Important values include:

```text
AUTH_COOKIE_NAME=team_session
AUTH_COOKIE_SECURE=false
AUTH_SESSION_HOURS=8
GITHUB_INTEGRATION_ENABLED=true
GITHUB_REPOSITORY=HoosseinRahimi/team-project
```

Set `AUTH_COOKIE_SECURE=true` when serving the application over HTTPS.

## Git workflow

`main` is the stable integration branch and should remain runnable for the professor at all times.

Normal work flow:

```text
main
  │
  └── feature/fix/docs branch
          │
          ▼
       commits
          │
          ▼
          PR
          │
       CI/review
          │
          ▼
      squash merge
          │
          ▼
         main
```

Branch naming:

```text
feature/<name>
fix/<name>
docs/<name>
refactor/<name>
test/<name>
chore/<name>
```

Rules:

- do not use direct `main` commits for normal development
- update your feature branch from `main` before final merge when needed
- resolve conflicts on the feature branch, not on `main`
- do not force-push `main`
- prefer focused PRs and squash merge
- keep unrelated work out of the same PR

Conventional Commit prefixes:

```text
feat: fix: docs: refactor: test: chore: ci: build:
```

## Project direction

The shared platform is intentionally implemented once. Team members do **not** build separate copies of Calendar, Timeline, Activity, Login, or Professor Dashboard.

Instead:

```text
Shared Platform
├── Authentication
├── Activity System
├── Calendar
├── Timeline
├── Student Dashboard
├── Professor Dashboard
├── GitHub Integration
└── Project Integration
      ├── Member A specialized project
      ├── Member B specialized project
      └── Member C specialized project
```

The next major platform feature is the controlled **Project Runner / Project Integration** layer, where member projects can be surfaced and eventually executed through an allowlisted, safe contract rather than arbitrary shell commands.

See [docs/project-contract.md](docs/project-contract.md).

## Documentation

- [Architecture](docs/architecture.md)
- [Authentication](docs/authentication.md)
- [GitHub integration](docs/github-integration.md)
- [Git workflow](docs/git-workflow.md)
- [Database rules](docs/database-rules.md)
- [Project contract](docs/project-contract.md)
- [Branch protection](docs/branch-protection.md)
- [Engineering quality](docs/engineering-quality.md)
- [Architecture decision records](docs/adr/)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Changelog](CHANGELOG.md)

## API conventions

- Prefix application routes with `/api/`
- Use plural resource names
- Use typed Pydantic request/response contracts
- Return structured errors
- Unknown resources → `404`
- Malformed input → `422`
- Unauthenticated → `401`
- Forbidden → `403`
- Never trust a frontend-provided user ID as proof of authorization
- Keep Git-tracked JSON authoritative for shared user/activity/project data
- Keep credentials, sessions, and secrets in runtime-only state
- Keep external integrations isolated, read-only where possible, and offline-safe
