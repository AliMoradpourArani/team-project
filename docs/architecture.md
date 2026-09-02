# Architecture

## Overview

The application is a modular monolith: one React/Vite frontend, one FastAPI backend, and one SQLite runtime database. It deliberately avoids microservices and distributed infrastructure.

The platform now combines four major concerns:

1. team activity/project management,
2. professor review/submission/release workflows,
3. GitHub-backed project intelligence,
4. governed AI planning, repository intelligence, and controlled automation.

## Major components

- `frontend/`: React + Vite + TypeScript UI, including the student AI cockpit.
- `backend/app/`: FastAPI routes, authentication, role/CSRF enforcement, observability, and application lifespan.
- `backend/services/`: activity/project logic, GitHub integration, AI agent, repository RAG, code review, debugging, health, orchestration, and automation.
- `backend/schemas/`: typed Pydantic API contracts.
- `backend/database/`: SQLite connection helpers and ordered append-only migrations.
- `data/`: Git-tracked authoritative shared users, activities, and project metadata.
- `projects/`: reviewed member-project source and typed demo manifests.

## State boundaries

The application intentionally separates state into four classes:

1. **Git-tracked shared state**: users, activities, and projects under `data/`. This remains authoritative across clones.
2. **Private/runtime SQLite state**: auth accounts, sessions, project-run history, professor evaluations, submissions/releases, AI threads/memory, repository chunks, governed AI actions, notifications, and related audit records.
3. **External read models**: GitHub repository/contribution data used for dashboards and intelligence.
4. **Governed external mutations**: optional GitHub branch/issue/PR writes performed only through the AI action approval pipeline using server-side credentials.

AI automation must never bypass the tracked activity-write contract. When progress changes are applied, they go through the same authoritative activity service that updates Git-tracked JSON and reconciles SQLite.

## Request and authorization boundary

FastAPI is the security boundary. React routing never grants authority.

- Student: own protected workspace, activities, projects, AI threads/memory/intelligence, and explicitly approved actions.
- Professor: team-wide dashboards, review/submission/release controls, and shared project inspection according to existing professor permissions.
- Unsafe authenticated requests require a valid session-specific CSRF token.
- AI project lookup verifies student/project ownership before retrieval or mutation.

## AI architecture

The AI layer is split into several services instead of one unrestricted agent:

- `ai_agent`: persistent project chat, snapshots, replanning, memory, briefs, and specialist review.
- `ai_autonomy`: lexical repository RAG, governed actions, GitHub evidence/progress sync, debugging, health scoring, notifications, and safety controls.
- `ai_code_review`: diff-aware review.
- `ai_multi_agent`: seven-specialist orchestration with provider-backed execution when configured and deterministic fallback otherwise.
- `ai_automation`: recurring maintenance loop for health/notifications and optional evidence-backed progress application.

The key mutation model is:

```text
AI/user proposes action
        ↓
authenticated pending record
        ↓
explicit user approval
        ↓
execute through allowlisted handler
        ↓
audit result persisted
```

## Repository intelligence

Repository indexing is bounded to approved roots and text/code file types. Chunks are stored in runtime SQLite and retrieval is explicitly reported as `lexical-rag`. This is not presented as an embedding/vector system.

## GitHub boundaries

Two GitHub paths exist and must not be confused:

### Read-only integration

`GITHUB_*` configuration powers dashboard/contribution intelligence and is designed to fail safely when GitHub is unavailable.

### Governed write integration

`AI_GITHUB_*` configuration is optional and server-only. It can create allowlisted GitHub branches, issues, and pull requests only after an authenticated propose -> approve -> execute flow.

No browser-provided token and no model-generated credential is accepted.

## Database approach

SQLite uses ordered plain SQL migrations. Merged migrations are append-only. Shared Git-visible data remains authoritative while runtime/private/AI state lives only in SQLite.

See `docs/database-rules.md`.

## Extension rules

- New backend feature: route in `backend/app/api/`, business logic in `backend/services/`.
- New protected mutation: enforce principal/CSRF and ownership server-side.
- New schema state: add a new numbered migration, never edit a merged migration.
- New external integration: trusted server configuration, bounded permissions, timeout/failure handling, and no secret exposure.
- New AI action: add a typed allowlisted action kind, explicit validation, audit result, and approval requirement before side effects.

See also `docs/ai-autonomy-platform.md`, `docs/authentication.md`, `docs/github-integration.md`, and `docs/adr/`.
