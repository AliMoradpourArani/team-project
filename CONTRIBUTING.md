# Contributing

## 0. Access prerequisites

`ForgeFlow-AI-Core` is a private production repository. Access is granted for authorized development work only.

Before a developer receives Core access, the Founder/Owner must have a completed onboarding record that includes the applicable Developer/IP/Confidentiality Agreement, a pre-existing IP disclosure, and an access authorization record. Signed legal documents and personal information must **not** be committed to this repository.

Repository access, commits, pull requests, authorship, contributor status, issue assignments, or technical responsibility do not by themselves grant equity, partnership rights, or ownership in ForgeFlow. Ownership and licence rights are governed by the applicable signed agreement.

Normal developers should receive the minimum repository role needed to contribute, normally **Write**, not Maintain or Admin. Access must be removed promptly when the engagement ends or no longer requires Core access.

See `docs/team-governance/developer-access-policy.md` and `docs/team-governance/legal-onboarding-checklist.md`.

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

## 7. Third-party and AI-assisted material

Do not introduce code, models, datasets, fonts, images, documentation, or other material unless the contributor has the right to use it for ForgeFlow and the applicable licence is compatible with the project's intended use. Copyleft, source-available, non-commercial, research-only, custom, or unclear licences require explicit review before inclusion.

AI-assisted output must be reviewed as code, not treated as automatically safe. Check provenance, licence risk, confidential-data exposure, secrets, security, correctness, and maintainability before committing it.

If a contribution contains the developer's pre-existing material, identify it before merge and record the applicable ownership/licence treatment through the legal onboarding process.

## 8. Resolve conflicts deliberately

Inspect both sides, preserve intended behavior, remove all conflict markers, and rerun affected tests. Lock files should be regenerated instead of deleted. Migration conflicts require schema review and normalized numbering.

## 9. Pull requests

Push the feature branch and open a PR to `main`. CI/security checks must pass. Changes should be reviewed by the applicable CODEOWNER. Squash merge is preferred for focused change sets.

Never use a PR checkbox as a substitute for a signed legal agreement. The PR template is an engineering/audit control only.

## 10. End of access

When a developer leaves the engagement or no longer needs Core access, the Owner should revoke repository and deployment access, rotate any credentials the developer could access, and complete the offboarding record. The developer must return or delete ForgeFlow confidential material as required by the applicable agreement.

## Definition of Done

A change is Done when implementation is complete, formatting/lint/types/tests/build are green, migrations and contracts are updated when required, environment/deployment changes are documented, security boundaries remain intact, third-party material is authorized, documentation reflects user-visible behavior, and `main` remains runnable after merge.
