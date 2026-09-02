# Team Project Community Showcase

A public-facing, sanitized edition of the Team Project platform.

The private upstream is a full project-management and AI engineering workspace built with FastAPI, React/TypeScript, SQLite, GitHub intelligence, governed AI actions, repository retrieval, code review/debugging, progress intelligence, health scoring, daily/weekly briefs, and multi-agent orchestration.

This public edition is intentionally narrower. It exists to demonstrate the product architecture, engineering practices, UX direction, and reusable concepts without publishing private team data, runtime state, credentials, submission artifacts, or internal operational details.

## Highlights

- Student and professor project workspaces
- Activity, timeline, calendar, project and review workflows
- GitHub contribution intelligence
- Persistent AI project copilot
- Repository retrieval with bounded lexical RAG
- Diff-aware AI/code-quality review surface
- AI debugging assistance
- Evidence-backed progress intelligence
- Project health scoring and daily/weekly intelligence
- Seven-specialist multi-agent orchestration
- Governed AI actions using propose -> approve -> execute
- CI, E2E, dependency audit, CodeQL and security controls

## Public vs private boundary

The public showcase does not contain:

- real team/user data
- runtime SQLite databases or sessions
- environment secrets or tokens
- private submissions or grading records
- production credentials
- private GitHub automation configuration
- internal-only deployment state

All configuration shown here uses placeholders only.

## Architecture

See `ARCHITECTURE.md` for the public architecture overview and `FEATURES.md` for the capability matrix.

## Security

See `SECURITY.md`. Never commit real AI or GitHub credentials.

## Release

This bundle represents the public showcase baseline for **v0.13.0**.

See `RELEASE_NOTES.md` for the stable milestone summary.

## License

MIT. See `LICENSE`.

## Private upstream

The production/development repository is intentionally private. This public edition is maintained as a curated release surface rather than a mirror of the private repository.
