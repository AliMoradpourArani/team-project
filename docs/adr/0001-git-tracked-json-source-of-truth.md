# ADR 0001: Git-tracked JSON is the shared source of truth

Status: Accepted
Date: 2026-09-01

## Context

The professor must be able to pull the repository and reproduce each student's
visible work locally. Committing a mutable SQLite database would create binary
merge conflicts, opaque history, and machine-specific state.

## Decision

Shared users, activities, and project metadata are stored as validated JSON under
`data/` and reviewed through Git. SQLite is a derived local runtime database built
from ordered migrations plus those tracked source files. Activity writes update
the authoritative JSON first and then reconcile SQLite.

## Consequences

- Team activity changes remain readable in commits and pull requests.
- Fresh clones can reproduce the runtime database deterministically.
- Database sync must remain idempotent and reconciliation-safe.
- APIs that mutate shared state must preserve the JSON contract rather than write
  only to SQLite.
- Large/high-frequency production workloads would eventually justify a different
  persistence model, but that is intentionally outside the university-project
  scope.
