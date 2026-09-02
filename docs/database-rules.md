# Database rules

The runtime database is local SQLite and is generated/private state, not the shared Git source of truth. Never commit it or copy another developer's database into the repository.

## Layers

1. **Schema migrations**: ordered SQL files in `backend/database/migrations/`.
2. **Git-tracked source data**: JSON under `data/`, authoritative for shared users, activities, and project metadata.
3. **Runtime/private SQLite state**: authentication, sessions, demo history, professor reviews, submissions/releases, AI conversations/memory, repository index chunks, governed AI actions, notifications, and other local audit/intelligence state.

## Commands

```bash
make db-init
make db-sync
make db-reset
```

`db-sync` reconciles Git-tracked shared source into SQLite. Runtime/private tables are not treated as replacements for `data/`.

## Migration rules

- Every schema change gets a new numbered SQL migration.
- Use a zero-padded prefix such as `013_description.sql`.
- Duplicate numeric prefixes are invalid.
- Never rewrite/delete a migration already merged into `main`.
- Resolve migration conflicts by preserving both intended schema changes and renumbering on the feature branch when necessary.

The current schema includes AI platform migrations after the original product/runtime migrations, including persistent AI threads, structured memory/GitHub links, repository chunks, action audit records, memory events, health snapshots, and notifications.

## Shared-data authority

For Git-shared activities and project metadata, `data/` is authoritative.

Activity mutations must follow:

```text
validated request / approved AI action
        ↓
authoritative activity write service
        ↓
data/activities/<user_id>/<date>.json
        ↓
SQLite reconciliation
```

AI progress automation is not allowed to update only SQLite. When `apply=true`, it goes through this same activity-write path.

## Runtime-only AI state

These classes of AI data intentionally remain outside tracked source data:

- chat threads/messages and thread memory,
- structured project memory and decision events,
- lexical repository RAG chunks,
- GitHub evidence-link records,
- proposed/approved/executed AI action audit records,
- health snapshots and notifications.

These records support local intelligence and auditability but do not redefine the shared project/task source of truth.

## Docker

Docker Compose bind-mounts `./data` read/write so authoritative activity edits remain visible to Git, mounts `./projects` read-only, and stores private SQLite state in the `team-runtime` volume.
