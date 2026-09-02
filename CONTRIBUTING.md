# Contributing

## 1. Create a branch

Do not develop normal features directly on `main`.

```bash
git switch main
git pull
git switch -c feature/<feature-name>
```

Use focused prefixes such as `feature/`, `fix/`, `docs/`, `refactor/`, or `test/`.

## 2. Keep the branch current

Merge the latest `main` into the feature branch and resolve conflicts there:

```bash
git switch feature/<feature-name>
git merge main
./scripts/test.sh
```

Do not force-push `main`.

## 3. Commit style

Use meaningful Conventional Commit-style messages:

```text
feat: add project health panel
fix: preserve activity source authority
docs: sync AI autonomy configuration
test: cover approved action execution
chore: update dependencies
```

## 4. Local checks

```bash
./scripts/test.sh
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check backend tests
npm run lint --prefix frontend
npm run type-check --prefix frontend
npm test --prefix frontend
npm run build --prefix frontend
```

## 5. Database migrations

Every schema change requires a new ordered migration. Never edit a migration already merged into `main`.

```bash
DATABASE_PATH=/tmp/mig-test.db .venv/bin/python -m backend.database.init_db --seed
```

See `docs/database-rules.md`.

## 6. AI/autonomy contribution rules

AI features have stricter invariants:

- never place model/provider/GitHub secrets in tracked files or frontend code,
- verify student/project ownership server-side before AI retrieval or mutation,
- durable/external AI side effects must use an explicit authenticated control path,
- new external action kinds belong in the typed allowlist and must participate in `propose -> approve -> execute`,
- automatic task/progress mutations must use the authoritative activity-write service rather than direct SQLite writes,
- repository RAG must remain bounded to approved roots/types/sizes,
- provider and external-network calls need timeout/failure handling,
- add tests proving an unapproved action cannot execute,
- document any new environment variable in `.env.example` and Docker/deployment configuration when applicable.

See `docs/ai-autonomy-platform.md` and `SECURITY.md`.

## 7. Resolve conflicts deliberately

Inspect both sides, preserve intended behavior, remove all conflict markers, and rerun affected tests. Lock files should be regenerated instead of deleted. Migration conflicts require schema review and normalized numbering.

## 8. Pull requests

Push the feature branch and open a PR to `main`. CI/security checks must pass. Squash merge is preferred for focused change sets.

## Definition of Done

A change is Done when implementation is complete, formatting/lint/types/tests/build are green, migrations and contracts are updated when required, environment/deployment changes are documented, security boundaries remain intact, documentation reflects user-visible behavior, and `main` remains runnable after merge.
