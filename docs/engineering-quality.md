# Engineering quality gates

The repository treats `main` as a continuously runnable integration branch. Pull requests are validated across backend, frontend, browser flows, database initialization, security tooling, and AI-specific contracts.

## Pull-request CI

The primary CI workflow covers:

1. unresolved conflict-marker detection,
2. backend Ruff linting,
3. AI reviewer script syntax validation,
4. backend pytest suite with coverage gate,
5. member-project onboarding contracts,
6. fresh SQLite initialization/source reconciliation,
7. final-delivery preflight smoke validation,
8. frontend ESLint and Prettier checks,
9. TypeScript type checking,
10. frontend unit tests and production build,
11. Playwright browser E2E flows against FastAPI + Vite.

AI/autonomy integration tests cover repository RAG, prompt-injection defense, governed action approval/execution, project isolation, authoritative task writes, GitHub evidence progress inference, health scoring, orchestration, and notifications.

## Security automation

`.github/workflows/security.yml` includes:

- dependency review when GitHub Dependency Graph is available,
- `pip-audit`,
- `npm audit`,
- CodeQL for Python when GitHub code scanning is available,
- CodeQL for JavaScript/TypeScript when GitHub code scanning is available.

The private upstream skips CodeQL by default because GitHub code-scanning upload may be unavailable for the repository/account configuration. To enable CodeQL on the private upstream after code scanning is enabled in GitHub, set the repository variable:

```text
ENABLE_CODEQL_ON_PRIVATE=true
```

Public repositories run the CodeQL matrix without that variable. Dependency and package audits continue regardless of this CodeQL gate.

Dependabot performs scheduled dependency updates.

## AI pull-request reviewer

`.github/workflows/ai-review.yml` uses trusted base-branch code and PR patch text. It does not execute pull-request code and does not have contents-write or merge permission.

Configure the optional Actions secret:

```text
OPENAI_API_KEY
```

and optionally the repository variable:

```text
OPENAI_REVIEW_MODEL=gpt-5.6-luna
```

If the reviewer secret is unavailable, the workflow reports a successful skip rather than blocking normal CI. A green AI Review workflow therefore means the workflow itself passed; confirm the secret is configured if an actual provider-backed review is required.

This Actions reviewer is separate from the in-app `AI_API_KEY` used by the project copilot/orchestrator.

## Runtime safety quality

AI features are expected to preserve these testable invariants:

- no side effect before action approval,
- no cross-student/project retrieval,
- no direct SQLite-only mutation of authoritative task state,
- no client-provided external credentials,
- bounded RAG/payload sizes,
- timeout/fallback behavior for provider and GitHub calls,
- automatic progress mutation disabled unless explicitly opted in.

## Observability

The API emits request IDs and structured request logs. AI action status/results and notifications are persisted in runtime state, giving important autonomy operations an auditable trail.

## CODEOWNERS and branch protection

High-risk platform paths are owned by `@HoosseinRahimi`. Recommended required checks and branch-protection settings are documented in `docs/branch-protection.md`.

## Local equivalents

```bash
make test
python -m pytest --cov=backend --cov-report=term-missing
npm audit --prefix frontend --audit-level=high
```

For Playwright, install the E2E dependencies and Chromium, initialize an isolated runtime DB, and run the browser suite from `e2e/`.
