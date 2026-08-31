# Team Project

Team Project is a local web application for a university team and their
professor. Team members get a personal page for daily activities, calendar
history, and projects; the professor gets a shared dashboard of the whole team.

This `main` branch is the **stable integration foundation**: landing page, team
member pages, read-only API, reproducible database bootstrap, and the contracts
every feature branch must follow. Calendar, timeline, authentication, advanced
Git integration, and project execution are future feature branches.

## Architecture

Modular monolith — no microservices:

- **Frontend:** React + Vite + **TypeScript** (`frontend/`)
- **Backend:** FastAPI with small route modules, services, and Pydantic schemas (`backend/`)
- **Database:** SQLite generated from ordered SQL migrations; the generated
  file is **never committed** (`backend/database/`)
- **Source data:** Git-tracked JSON files under `data/` are the **authoritative
  shared source** for users, activities, and projects
- **Docker:** Compose runs one backend and one frontend container locally

See [docs/architecture.md](docs/architecture.md) for details.

## Repository structure

```text
team-project/
├── frontend/                 # React/Vite/TypeScript application
│   └── src/{components,types.ts,api.ts,App.tsx,main.tsx}
├── backend/
│   ├── app/                  # FastAPI app; routes in app/api/*.py
│   ├── schemas/              # Pydantic request/response + data validation
│   ├── services/             # Business logic / queries
│   └── database/
│       ├── migrations/       # Ordered SQL migrations (committed)
│       ├── connection.py     # SQLite connection helpers
│       ├── init_db.py        # Create DB + apply migrations (+ --seed)
│       ├── sync_data.py      # Idempotent sync of data/ into the DB
│       └── source_files.py   # Validated loader for data/ files
├── data/                     # AUTHORITATIVE shared team data (Git-tracked)
│   ├── users/<id>.json
│   ├── activities/<user_id>/<date>.json
│   └── projects/<id>.json
├── projects/<owner>/<name>/  # Student projects with project.json manifests
├── scripts/                  # setup, test, reset, conflict-marker check
├── docs/                     # architecture, git workflow, database rules, contracts
├── tests/                    # Backend/API/database tests
├── .github/                  # CI workflow + PR template
├── docker-compose.yml
└── Makefile                  # Convenience wrappers (see below)
```

## Prerequisites

- Git
- Python 3.11+ (3.12+ recommended)
- Node.js 20+ and npm
- Docker (optional, for the container workflow)

## Quick setup (native)

```bash
git clone <repository-url> team-project
cd team-project
make setup          # or: ./scripts/setup.sh
```

This creates `.venv`, installs backend and frontend dependencies, and builds
the database from migrations with the tracked data.

## Database initialization and synchronization

```bash
make db-init        # create DB from scratch, apply migrations (schema only)
make db-sync        # idempotently load Git-tracked data/ into the DB
make db-reset       # delete the local dev database (safe, fixed path)

# equivalent direct commands:
.venv/bin/python -m backend.database.init_db --seed
.venv/bin/python -m backend.database.sync_data
```

Running sync repeatedly never duplicates records. The Git-tracked files under
`data/` are authoritative; the SQLite file is derived local state and is
ignored by Git. See [docs/database-rules.md](docs/database-rules.md).

## Run the backend

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload
```

API at <http://localhost:8000> — `GET /api/health`, `/api/users`,
`/api/users/{id}`, `/api/activities`, `/api/projects`. Interactive docs:
<http://localhost:8000/docs>.

## Run the frontend

```bash
npm run dev --prefix frontend
```

Open <http://localhost:5173>. Member routes: `/users/hossein`, `/users/ali`,
`/users/reza`. Override the backend URL with `VITE_API_BASE_URL` (see
`.env.example`).

## Run tests

```bash
make test           # or ./scripts/test.sh — full integration check
```

Individual checks:

```bash
.venv/bin/python -m pytest -q                       # backend tests
.venv/bin/python -m ruff check backend tests        # backend lint
npm run lint --prefix frontend                      # frontend lint
npm run type-check --prefix frontend                # frontend types
npm test --prefix frontend                          # frontend unit tests
```

## Docker

```bash
docker compose up --build
```

Then open <http://localhost:5173>. Stop with `Ctrl+C` or `docker compose down`.

## Git workflow

`main` is the stable integration branch — never commit features directly.
Branches: `feature/<name>`, `fix/<name>`, `docs/<name>`, `refactor/<name>`,
`test/<name>`. Update feature branches with `git merge main`; open Pull
Requests into `main` (squash merge by default). Full rules:

- [CONTRIBUTING.md](CONTRIBUTING.md) — branch, commit, test, migration, and PR workflow
- [docs/git-workflow.md](docs/git-workflow.md) — branch model and conflict rules
- [docs/database-rules.md](docs/database-rules.md) — migrations and data authority
- [docs/project-contract.md](docs/project-contract.md) — `data/` file and project manifest contracts
- [docs/branch-protection.md](docs/branch-protection.md) — recommended GitHub settings for `main`

## API conventions

- Prefix all routes with `/api/`, use plural nouns (`/api/users`)
- Typed Pydantic request/response models; structured errors; no stack traces
- Unknown user/project → 404; malformed input → 422
