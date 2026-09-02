# Repository-wide pull request review instructions

Review every pull request as a production-quality code review. Prioritize concrete defects over style preferences.

## Blocking findings

Request changes for:
- security vulnerabilities, leaked credentials, unsafe authentication/authorization, injection risks, or privilege escalation;
- logic errors, broken error handling, data corruption, race conditions, or invalid state transitions;
- breaking API/data-contract changes without the required migration, compatibility handling, documentation, or tests;
- changes that make a fresh clone, database initialization, CI, or the documented demo/submission workflow fail;
- important new behavior with no meaningful automated tests.

## Project invariants

- Git-tracked JSON under `data/` is the authoritative shared state.
- SQLite is derived runtime state and must remain reproducible and idempotent.
- Merged SQL migrations are append-only. Do not rewrite migration history.
- Stable IDs and foreign-key relationships must remain valid.
- Do not introduce arbitrary shell or project execution paths.
- Treat `.github/`, database code, schemas, dependencies, authentication, authorization, and execution code as high-risk.

## Review output

- Point to the exact file and line when possible.
- Explain why each blocking issue matters and give a concrete fix.
- Distinguish blocking defects from optional suggestions.
- Check tests, linting, type safety, security, maintainability, and architecture consistency.
- Do not approve a PR with a known blocking defect.
