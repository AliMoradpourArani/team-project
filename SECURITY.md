# Security policy

This repository is a university team project, but security-sensitive changes are reviewed with production-style discipline.

## Reporting a vulnerability

Do not post credentials, API keys, tokens, private student data, or a working exploit in a public issue. Contact the repository owner privately and include the affected component, impact, minimal reproduction, and suggested mitigation when known.

## Repository security rules

- Never commit secrets. Keep passwords/tokens/API keys in local/server secret stores or GitHub Actions secrets.
- Pull-request code must not receive trusted secrets while it is being executed.
- `pull_request_target` workflows may execute only trusted base-branch code.
- Database migrations are append-only after merge.
- Project runner features use explicit typed allowlists and never execute arbitrary shell text from tracked manifests.
- High-risk paths remain CODEOWNERS-protected.

## AI and autonomy boundaries

The in-app AI layer follows additional rules:

- AI output is not authority. External or durable actions follow explicit authenticated control paths.
- Governed actions use `propose -> approve -> execute`; pending actions have no side effects.
- GitHub write actions require server-only `AI_GITHUB_TOKEN` and `AI_GITHUB_REPOSITORY` configuration.
- Browser-provided and model-generated credentials are never accepted as GitHub write authority.
- Automatic evidence-backed progress mutation is opt-in through `AI_AUTOMATION_APPLY_PROGRESS`; the default is false.
- Applied task/progress changes go through the authoritative Git-tracked activity write service rather than mutating SQLite directly.
- Repository RAG reads only allowlisted repository roots/file types and applies bounded file/query/payload sizes.
- AI chat applies request-rate controls and rejects common prompt-injection/secret-exfiltration patterns before provider calls.
- Provider/GitHub network requests use bounded timeouts and local-safe fallbacks where applicable.
- AI action execution results and failures are persisted for auditability.

## Secret separation

The project uses separate credentials for separate capabilities:

- `GITHUB_TOKEN`: optional read-only dashboard/integration access.
- `AI_API_KEY`: optional model-provider access for in-app AI.
- `AI_GITHUB_TOKEN`: optional governed GitHub write access. Give it only the repository permissions needed for the allowlisted branch/issue/PR operations.
- `OPENAI_API_KEY`: optional GitHub Actions secret for the repository AI PR reviewer. It is independent from the in-app provider key.

Never place real values in `.env.example`, tracked JSON, project manifests, README files, frontend environment variables, or client-side code.

## Automated checks

Pull requests are covered by backend/frontend CI, browser E2E, dependency audits, CodeQL, conflict-marker checks, and the optional AI PR review workflow. The repository AI reviewer reads patch text but has no repository contents-write or merge permission.

See `docs/ai-autonomy-platform.md`, `docs/engineering-quality.md`, and `docs/branch-protection.md`.
