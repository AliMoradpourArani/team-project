# Architecture

## Overview

The project is a **modular monolith**: one FastAPI backend, one React frontend, and one SQLite runtime database. No microservices, queues, or distributed infrastructure.

- **Frontend** (`frontend/`): React + Vite + TypeScript. Shared types live in `src/types.ts`, the credential-aware API client in `src/api.ts`, and UI modules under `src/components/`.
- **Backend** (`backend/`):
  - `app/` - FastAPI application, API routes, request observability, authentication/role/CSRF dependencies.
  - `auth/` - local account bootstrap CLI.
  - `schemas/` - Pydantic HTTP/auth/source-data/GitHub read-model contracts.
  - `services/` - authentication/session logic, professor aggregation, GitHub aggregation, queries, tracked activity writes.
  - `database/` - connection helpers, ordered SQL migrations, init/seed/sync commands.
- **Data** (`data/`): Git-tracked source of truth for shared team information (users, activities, projects), including optional explicit GitHub identity mappings.
- **Student projects** (`projects/<owner>/<project>/`): runnable member projects with a `project.json` manifest.

## State boundaries

The application intentionally has three kinds of state/data:

1. **Shared Git-tracked state**: users, activities, and projects under `data/`. This is authoritative across clones and is synchronized into SQLite.
2. **Private runtime state**: authentication accounts and sessions. These exist only in SQLite and must never be synchronized into Git-tracked JSON.
3. **External read models**: GitHub repository activity. This is fetched on demand, cached briefly, and is never authoritative for project state.

This boundary lets the professor clone and reproduce project data while keeping passwords and sessions private and making external analytics optional/offline-safe.

## Database approach

We deliberately use **SQLite with ordered plain-SQL migrations** instead of SQLAlchemy + Alembic. For a student team the stdlib `sqlite3` approach is simple to understand and debug while still giving deterministic, reviewable schema evolution.

- All application timestamps are UTC.
- Activity dates are explicit ISO-8601 dates (`YYYY-MM-DD`).
- Shared project primary keys are stable text slugs.
- Authentication accounts use integer runtime IDs; session tokens are stored only as SHA-256 digests.
- `users.github_username` is derived from the optional Git-tracked user mapping.
- Merged migrations are append-only.

See `docs/database-rules.md`.

## Authentication boundary

FastAPI is the security boundary. React route selection never grants access.

- Public: health endpoints and login.
- Student: own profile, own activities, own projects; own activity writes only.
- Professor: all shared data plus professor dashboards; read-only.
- Session: server-side SQLite session + HttpOnly cookie.
- Unsafe request protection: session-specific CSRF token in `X-CSRF-Token`.

See `docs/authentication.md` and `docs/adr/0002-server-side-cookie-sessions.md`.

## GitHub integration boundary

GitHub is treated as a read-only external dependency, not as project authority.

- professor-only endpoint: `GET /api/professor/github`
- fixed API host: `https://api.github.com`
- trusted runtime configuration chooses one repository
- tracked `github_username` explicitly maps users to GitHub logins
- no request parameter can select an arbitrary repository or GitHub identity
- three API requests per refresh maximum: repository metadata, recent commits, recent PRs
- short in-process TTL cache reduces latency and rate-limit pressure
- failures return an `unavailable` response without affecting the core professor dashboard
- E2E disables the external call; deterministic unit tests verify aggregation

See `docs/github-integration.md` and `docs/adr/0003-github-integration-read-model.md`.

## Extension points

- **New backend feature:** add `backend/app/api/<feature>.py`, register it in `backend/app/main.py`, and keep business logic in `backend/services/`.
- **New protected route:** start from `get_current_principal`, `require_professor`, or `require_csrf`; never authorize from request JSON alone.
- **New frontend feature:** add a component under `frontend/src/components/` and reuse `src/api.ts` so credentials/CSRF behavior stays centralized.
- **New external integration:** isolate it behind a service/read model, use trusted configuration, fail safely, and keep core shared data authoritative.
- **New schema change:** add a new numbered SQL migration. Never edit an already-merged migration.
- **New shared data:** add files under `data/` following `docs/project-contract.md`, then run `make db-sync`.
