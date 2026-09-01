# Team Project

Team Project is a local web application for a university team and their professor. Students get a protected personal dashboard for daily activities, calendar history, timeline, and projects. Professors get a read-only overview across the team with per-member progress and recent activity.

The shared platform now includes:

- **Phase 1:** reproducible FastAPI/React/SQLite foundation and Git workflow
- **Phase 2:** activity CRUD, calendar, timeline, user dashboard, Git-tracked activity writes
- **Phase 2.5:** E2E, coverage, security scanning, CODEOWNERS, Dependabot, observability, optional AI PR reviewer
- **Phase 3:** local authentication, student/professor authorization, CSRF protection, and professor dashboard

Advanced Git contribution analytics and project execution remain future features.

## Architecture

Modular monolith, no microservices:

- **Frontend:** React + Vite + TypeScript (`frontend/`)
- **Backend:** FastAPI with route modules, auth dependencies, services, and Pydantic schemas (`backend/`)
- **Database:** SQLite generated from ordered SQL migrations; the generated file is never committed
- **Source data:** Git-tracked JSON under `data/` remains authoritative shared state for users, activities, and projects
- **Authentication state:** accounts and sessions live only in runtime SQLite and are never Git-tracked
- **Docker:** Compose bind-mounts `./data` and persists runtime auth/database state in a named volume

See [docs/architecture.md](docs/architecture.md), [docs/authentication.md](docs/authentication.md), and [docs/adr/](docs/adr/).

## Repository structure

```text
team-project/
├── frontend/                 # React/Vite/TypeScript application
│   └── src/{components,types.ts,api.ts,App.tsx,main.tsx}
├── backend/
│   ├── auth/                 # Local account bootstrap CLI
│   ├── app/                  # FastAPI app, routes, auth dependencies, observability
│   ├── schemas/              # API/auth/source-data contracts
│   ├── services/             # Auth, professor aggregation, queries, activity writes
│   └── database/
│       ├── migrations/       # Ordered SQL migrations (committed)
│       ├── connection.py
│       ├── init_db.py
│       ├── sync_data.py
│       └── source_files.py
├── data/                     # AUTHORITATIVE shared team data (Git-tracked)
│   ├── users/<id>.json
│   ├── activities/<user_id>/<date>.json
│   └── projects/<id>.json
├── e2e/                      # Playwright student + professor browser flows
├── projects/<owner>/<name>/  # Student projects with project.json manifests
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

- Git
- Python 3.11+ (3.12+ recommended)
- Node.js 20+ and npm
- Docker (optional)

## Quick setup (native)

```bash
git clone <repository-url> team-project
cd team-project
make setup
```

Then create login accounts locally:

```bash
make auth-bootstrap
```

Run it once for each student who needs access and once for the professor account. Student accounts must link to an existing tracked user id such as `hossein`, `ali`, or `reza`.

Passwords and password hashes must never be committed to Git. See [docs/authentication.md](docs/authentication.md).

## Database initialization and synchronization

```bash
make db-init        # create DB and apply migrations
make db-sync        # reconcile Git-tracked data/ into SQLite
make db-reset       # delete the local native development database
```

Equivalent commands:

```bash
.venv/bin/python -m backend.database.init_db --seed
.venv/bin/python -m backend.database.sync_data
```

Git-tracked files under `data/` are authoritative for shared project data. SQLite is derived for users/activities/projects but also holds private local authentication accounts and sessions. Activity writes through the web/API update tracked JSON and then reconcile SQLite.

## Authentication and roles

### Student

- signs in with a local account linked to one tracked user
- sees only their own user/profile, activities, and projects
- can create, edit, and delete only their own activities
- cannot access the professor dashboard or another student's API data

### Professor

- signs in with a local professor account
- sees all students, activities, projects, completion totals, and recent work
- can drill into each student's dashboard
- is intentionally read-only

Session cookies are HttpOnly and SameSite=Lax. Unsafe requests also require an in-memory CSRF token through `X-CSRF-Token`.

Auth endpoints:

```text
POST /api/auth/login
GET  /api/auth/me
POST /api/auth/logout
GET  /api/professor/dashboard
```

## Run the backend

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload
```

API: <http://localhost:8000>  
Interactive docs: <http://localhost:8000/docs>

Core protected endpoints:

```text
GET    /api/users
GET    /api/users/{id}
GET    /api/activities
POST   /api/activities
PUT    /api/activities/{activity_id}
DELETE /api/activities/{activity_id}
GET    /api/projects
```

`GET /api/health` and legacy `GET /health` remain public health checks.

Every API response receives an `X-Request-ID` correlation header and request metadata is logged as structured JSON.

## Run the frontend

```bash
npm run dev --prefix frontend
```

Open <http://localhost:5173>. Unauthenticated visitors see the login page. Students are routed to their own dashboard. Professors are routed to `/professor` and can open read-only member details.

## Run tests

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

CI enforces backend coverage and runs real Chromium E2E flows for both student authentication/activity management and professor read-only access. Security workflows also run dependency audits and CodeQL.

## Docker

```bash
docker compose up -d --build
docker compose exec backend python -m backend.auth.bootstrap
```

Repeat the bootstrap command for each account, then open <http://localhost:5173>.

Compose bind-mounts `./data:/app/data`, so student activity changes remain visible to Git. Runtime SQLite/auth state is stored in the `team-runtime` named volume so credentials and sessions survive container recreation without entering the repository.

Stop with:

```bash
docker compose down
```

Use `docker compose down -v` only when you intentionally want to delete local runtime auth/database state.

## Configuration

See `.env.example`.

Important auth settings:

```text
AUTH_COOKIE_NAME=team_session
AUTH_COOKIE_SECURE=false
AUTH_SESSION_HOURS=8
```

Set `AUTH_COOKIE_SECURE=true` when the application is served over HTTPS.

## Git workflow

`main` is the stable integration branch. Never commit features directly.
Branches: `feature/<name>`, `fix/<name>`, `docs/<name>`, `refactor/<name>`, `test/<name>`, `chore/<name>`. Open Pull Requests into `main` and use squash merge by default.

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [docs/git-workflow.md](docs/git-workflow.md)
- [docs/database-rules.md](docs/database-rules.md)
- [docs/authentication.md](docs/authentication.md)
- [docs/project-contract.md](docs/project-contract.md)
- [docs/branch-protection.md](docs/branch-protection.md)
- [docs/engineering-quality.md](docs/engineering-quality.md)
- [docs/adr/](docs/adr/)
- [SECURITY.md](SECURITY.md)
- [CHANGELOG.md](CHANGELOG.md)

## API conventions

- Prefix routes with `/api/` and use plural resource nouns
- Typed Pydantic request/response models and structured errors
- Unknown resources -> 404; malformed input -> 422; unauthenticated -> 401; forbidden -> 403
- Never use a frontend-supplied user id as authorization proof
- Git-tracked JSON remains authoritative for shared user/activity/project state
- Authentication credentials and sessions remain private runtime state
