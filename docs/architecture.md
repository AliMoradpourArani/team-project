# Architecture

## Overview

The project is a **modular monolith**: one FastAPI backend, one React frontend, and one SQLite runtime database. No microservices, queues, or distributed infrastructure.

- **Frontend** (`frontend/`): React + Vite + TypeScript. Shared types live in `src/types.ts`, the credential-aware API client in `src/api.ts`, and UI modules under `src/components/`.
- **Backend** (`backend/`):
  - `app/` - FastAPI application, API routes, request observability, authentication/role/CSRF dependencies.
  - `auth/` - local account bootstrap CLI.
  - `schemas/` - Pydantic HTTP/auth/source-data contracts.
  - `services/` - authentication/session logic, professor aggregation, queries, tracked activity writes.
  - `database/` - connection helpers, ordered SQL migrations, init/seed/sync commands.
- **Data** (`data/`): Git-tracked source of truth for shared team information (users, activities, projects).
- **Student projects** (`projects/<owner>/<project>/`): runnable member projects with a `project.json` manifest.

## State boundaries

The application intentionally has two kinds of state:

1. **Shared Git-tracked state**: users, activities, and projects under `data/`. This is authoritative across clones and is synchronized into SQLite.
2. **Private runtime state**: authentication accounts and sessions. These exist only in SQLite and must never be synchronized into Git-tracked JSON.

This boundary lets the professor clone and reproduce project data while keeping passwords and sessions private to each runtime.

## Database approach

We deliberately use **SQLite with ordered plain-SQL migrations** instead of SQLAlchemy + Alembic. For a student team the stdlib `sqlite3` approach is simple to understand and debug while still giving deterministic, reviewable schema evolution.

- All application timestamps are UTC.
- Activity dates are explicit ISO-8601 dates (`YYYY-MM-DD`).
- Shared project primary keys are stable text slugs.
- Authentication accounts use integer runtime IDs; session tokens are stored only as SHA-256 digests.
- Merged migrations are append-only.

See `docs/database-rules.md`.

## Authentication boundary

FastAPI is the security boundary. React route selection never grants access.

- Public: health endpoints and login.
- Student: own profile, own activities, own projects; own activity writes only.
- Professor: all shared data plus professor dashboard; read-only.
- Session: server-side SQLite session + HttpOnly cookie.
- Unsafe request protection: session-specific CSRF token in `X-CSRF-Token`.

See `docs/authentication.md` and `docs/adr/0002-server-side-cookie-sessions.md`.

## Extension points

- **New backend feature:** add `backend/app/api/<feature>.py`, register it in `backend/app/main.py`, and keep business logic in `backend/services/`.
- **New protected route:** start from `get_current_principal`, `require_professor`, or `require_csrf`; never authorize from request JSON alone.
- **New frontend feature:** add a component under `frontend/src/components/` and reuse `src/api.ts` so credentials/CSRF behavior stays centralized.
- **New schema change:** add a new numbered SQL migration. Never edit an already-merged migration.
- **New shared data:** add files under `data/` following `docs/project-contract.md`, then run `make db-sync`.
