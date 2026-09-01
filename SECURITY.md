# Security policy

This repository is a university team project, but security-sensitive changes are
reviewed with the same discipline as production code.

## Reporting a vulnerability

Do not post credentials, API keys, tokens, private student data, or a working
exploit in a public issue. Contact the repository owner privately and include:

- affected component or file
- impact and realistic attack path
- minimal reproduction steps
- suggested mitigation, if known

## Repository security rules

- Never commit secrets. Use GitHub Actions secrets and `.env` files ignored by Git.
- Pull-request code must not receive trusted secrets while it is being executed.
- `pull_request_target` workflows may only execute trusted base-branch code.
- Dependency changes must pass automated dependency review and audit checks.
- Database migrations are append-only after merge.
- Project runner features must use an explicit allowlist and must never execute arbitrary shell text from tracked data.
- High-risk paths are protected by `.github/CODEOWNERS`.

## Automated checks

The repository uses dependency review, `pip-audit`, `npm audit`, CodeQL, CI tests,
and a read-only AI pull-request reviewer. The AI reviewer receives PR patch text
but has no permission to modify repository contents or merge pull requests.
