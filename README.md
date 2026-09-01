# Team Project

A local-first university team platform for recording daily work, presenting individual progress, integrating reviewed member projects, and giving the professor a clear team view.

The application is one shared platform, not one duplicated website per student. User-specific behavior is driven by authenticated identity, `user_id`, tracked data, and project manifests.

## Current status

| Phase | Status | What it adds |
| --- | --- | --- |
| Phase 1 | ✅ Complete | FastAPI/React/SQLite foundation, migrations, reproducible setup, Git workflow |
| Phase 2 | ✅ Complete | Activity CRUD, calendar, timeline, personal dashboard, Git-tracked activity writes |
| Phase 2.5 | ✅ Complete | E2E, coverage gates, security scanning, CODEOWNERS, Dependabot, observability, optional AI PR review |
| Phase 3 | ✅ Complete | Local authentication, student/professor authorization, CSRF protection, professor dashboard |
| Phase 4 | ✅ Complete | Read-only GitHub integration, repository status, commit/PR metrics, contribution timeline |
| Phase 5 | ✅ Complete | Validated controlled Project Integration / Runner |
| Phase 6 | ✅ Complete | Generic member-project detail pages, health checks, safe README view, runtime demo history, integration checklist |

## What the platform does

### Student

Each student signs in to one protected workspace and can:

- view their profile and dashboard,
- create/edit/complete/delete their own activities,
- browse work through calendar and timeline views,
- inspect their own projects and integration status,
- open a generic project page at `/projects/<project_id>`,
- see project health checks and README documentation,
- run their reviewed project demo when the runner is explicitly enabled,
- see recent local demo history.

Students cannot access another student's protected data or project by changing a URL or API parameter.

### Professor

The professor can:

- view team progress and recent activities,
- drill into member dashboards,
- inspect all member projects and integration health,
- view repository/GitHub contribution signals,
- open every project's detail page,
- run reviewed project demos when local execution is enabled.

The professor remains read-only for shared student data.

## Architecture

The application is a **modular monolith**.

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
          ┌───────────────────────┬───────────┴─────────────┐
          │                       │                         │
   Git-tracked JSON            SQLite                  GitHub API
   shared source data       runtime/private state     read-only data
          │                       │
          │                       └── project run history
          │
          └── projects/<owner>/<project>/
                     │
                     ├── project.json
                     ├── README.md
                     └── validated runner entry point
```

Core technology:

- **Frontend:** React + Vite + TypeScript
- **Backend:** FastAPI + Pydantic
- **Database:** SQLite with ordered append-only SQL migrations
- **Shared source:** Git-tracked JSON under `data/`
- **Authentication:** Argon2 + server-side sessions + CSRF
- **GitHub integration:** read-only API client with short cache
- **Project integration:** validated manifest + generic detail read model + controlled runner
- **Testing:** pytest, Vitest, Playwright
- **Quality/security:** Ruff, ESLint, Prettier, TypeScript, dependency audits, CodeQL

## Source of truth

Shared data stays Git-visible:

```text
data/
├── users/<user_id>.json
├── activities/<user_id>/<date>.json
└── projects/<project_id>.json
```

SQLite is derived/runtime state. It also stores private local authentication state and project demo run history.

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
│   ├── app/                   # FastAPI routes/dependencies
│   ├── schemas/               # API/source/auth/integration contracts
│   ├── services/              # Business logic and integrations
│   └── database/              # SQLite migrations/init/sync
├── data/                      # Authoritative shared metadata
├── projects/<owner>/<name>/   # Reviewed member project source
├── e2e/                       # Playwright flows
├── tests/                     # Backend tests
├── docs/
├── .github/
├── CHANGELOG.md
├── SECURITY.md
├── docker-compose.yml
└── Makefile
```

## Quick start

Prerequisites: Git, Python 3.11+, Node.js 20+, npm. Docker is optional.

```bash
git clone https://github.com/HoosseinRahimi/team-project.git
cd team-project
make setup
make db-init
make db-sync
make auth-bootstrap
```

Run `make auth-bootstrap` once per student and once for the professor. A student account must link to an existing tracked `user_id`.

Backend:

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload
```

Frontend:

```bash
npm run dev --prefix frontend
```

Open:

- App: <http://localhost:5173>
- API: <http://localhost:8000>
- FastAPI docs: <http://localhost:8000/docs>

### Docker

```bash
docker compose up -d --build
docker compose exec backend python -m backend.auth.bootstrap
```

Docker mounts:

```text
./data     -> /app/data       (read/write, Git-visible shared data)
./projects -> /app/projects   (read-only reviewed project source)
team-runtime -> /app/runtime  (private SQLite/auth/runtime state)
```

## Authentication and authorization

### Student

- linked to exactly one tracked user,
- reads only their own protected user/activity/project data,
- modifies only their own activities,
- can inspect/run only their own visible project.

### Professor

- views all members and project/activity summaries,
- drills into member/project details,
- views GitHub contribution analytics,
- can invoke reviewed demos when execution is enabled,
- does not receive normal shared-data write access.

Authentication endpoints:

```text
POST /api/auth/login
GET  /api/auth/me
POST /api/auth/logout
```

Unsafe authenticated requests require `X-CSRF-Token`.

## Activities

```text
GET    /api/activities
POST   /api/activities
PUT    /api/activities/{activity_id}
DELETE /api/activities/{activity_id}
```

Activity writes update authoritative Git-tracked JSON and then reconcile SQLite.

## GitHub integration

Optional GitHub identity is explicit in tracked user data:

```json
{
  "id": "hossein",
  "display_name": "Hossein",
  "role": "Developer",
  "github_username": "HoosseinRahimi"
}
```

The application never guesses GitHub accounts from names or emails.

Runtime configuration:

```text
GITHUB_INTEGRATION_ENABLED=true
GITHUB_REPOSITORY=HoosseinRahimi/team-project
GITHUB_CACHE_TTL_SECONDS=60
GITHUB_API_TIMEOUT_SECONDS=5
```

A runtime-only read token may be supplied as `GITHUB_TOKEN`. Never commit it.

## Member Project Integration

A member project has two linked pieces:

1. authoritative metadata: `data/projects/<project_id>.json`
2. reviewed project source: `projects/<owner>/<project-directory>/`

Required project source layout:

```text
projects/<owner>/<project-directory>/
├── project.json
├── README.md
└── main.py
```

Example manifest:

```json
{
  "id": "team-foundation",
  "name": "Team Project Foundation",
  "owner_id": "hossein",
  "description": "Runnable demonstration for the shared platform.",
  "technology": ["python"],
  "project_type": "cli",
  "runner": "python-script-v1",
  "entry_point": "main.py",
  "repository_path": "projects/hossein/team-platform"
}
```

The current runner intentionally supports only:

```text
project_type = cli
runner       = python-script-v1
```

Do not add student-specific Core routes. A normal project automatically uses:

```text
/users/<user_id>
└── Projects
     └── /projects/<project_id>
```

### Project detail page

`/projects/<project_id>` exposes:

- authoritative project metadata,
- integration state,
- independent health checks,
- safe plain-text README preview,
- controlled demo action,
- recent local runtime history.

Health currently checks:

```text
Tracked project metadata
Manifest
Owner mapping
Repository / entry-point paths
Runner contract
README
```

Project endpoints:

```text
GET  /api/projects
GET  /api/projects/integrations
GET  /api/projects/{project_id}/detail
POST /api/projects/{project_id}/run
```

Demo history is stored only in runtime SQLite. It is never written into Git-tracked project data or source.

### Runner safety boundary

Execution is disabled by default:

```text
PROJECT_RUNNER_ENABLED=false
PROJECT_RUNNER_TIMEOUT_SECONDS=5
PROJECT_RUNNER_OUTPUT_LIMIT=16000
```

After code passes normal PR/CI/review:

```bash
export PROJECT_RUNNER_ENABLED=true
```

The backend derives argv, uses `shell=False`, validates ownership/paths, rejects free-form manifest commands, bounds runtime/output, and mounts project source read-only in Docker.

This is **not a sandbox for hostile code**. Only reviewed repository code should be enabled.

## Member integration checklist

Before a teammate opens a project PR:

```text
[ ] data/projects/<project_id>.json exists
[ ] owner_id is correct
[ ] project.json validates
[ ] repository_path exactly matches the directory
[ ] README.md documents purpose/setup/input/output/demo
[ ] entry point exists inside the project
[ ] no secrets are committed
[ ] no run/build/command shell fields are present
[ ] tests pass
[ ] CI + security checks are green
```

See [projects/README.md](projects/README.md) for the handoff contract.

## Database commands

```bash
make db-init
make db-sync
make db-reset
```

Merged migrations are append-only. Never rewrite a migration already on `main`.

## Testing and quality gates

```bash
make test
```

CI covers:

- conflict-marker detection,
- backend Ruff/tests/coverage + fresh DB sync,
- frontend ESLint/Prettier/TypeScript/unit/build,
- Playwright Chromium E2E,
- Python/npm dependency audits,
- CodeQL for Python and JavaScript/TypeScript.

Executable project paths remain CODEOWNERS-protected.

## Git workflow

`main` must remain runnable for the professor.

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

Rules:

- no normal direct development on `main`,
- resolve conflicts on the feature branch,
- no force-push to `main`,
- prefer focused PRs and squash merge,
- executable project code must pass review/CI before runner enablement.

## Documentation

- [Architecture](docs/architecture.md)
- [Authentication](docs/authentication.md)
- [GitHub integration](docs/github-integration.md)
- [Project contract](docs/project-contract.md)
- [Project runner](docs/project-runner.md)
- [Member project integration](docs/member-project-integration.md)
- [Git workflow](docs/git-workflow.md)
- [Database rules](docs/database-rules.md)
- [Engineering quality](docs/engineering-quality.md)
- [Architecture decisions](docs/adr/)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Changelog](CHANGELOG.md)

## API conventions

- prefix application routes with `/api/`,
- use typed Pydantic request/response contracts,
- unknown resources -> `404`, malformed input -> `422`, unauthenticated -> `401`, forbidden -> `403`,
- never trust a frontend-provided user id as authorization proof,
- keep Git-tracked JSON authoritative for shared team data,
- keep credentials/sessions/secrets/runtime history outside Git,
- keep external integrations isolated/read-only where possible,
- never introduce arbitrary shell execution through project manifests.
