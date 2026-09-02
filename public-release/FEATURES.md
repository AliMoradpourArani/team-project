# Public Feature Matrix

## Core workspace

- Role-aware student/professor experience
- Activities with planned / in-progress / completed lifecycle
- Calendar and timeline views
- Project detail pages and integration readiness
- Project review/evaluation workflow
- Immutable submission and release-preflight concepts

## GitHub intelligence

- Repository status and contribution summaries
- Commit and pull-request activity
- Activity-to-GitHub evidence linking
- Progress inference from linked implementation evidence

## AI engineering workspace

- Persistent project chat and project snapshots
- Roadmap replanning and task suggestions
- Project memory and decision memory
- Repository indexing and lexical retrieval-augmented context
- Diff-aware code-review analysis
- Log/error debugging assistance
- Project health scoring
- Daily and weekly intelligence briefs
- Notifications derived from project state
- Seven specialist roles: planner, project manager, code reviewer, debugger, progress tracker, GitHub agent, documentation agent

## Governed actions

AI actions use a controlled lifecycle:

1. propose
2. approve
3. execute

Supported internal concepts include task creation, progress updates, decision recording and GitHub evidence linking. External GitHub write operations are intentionally server-controlled and require runtime credentials in the private deployment.

## Engineering quality

- FastAPI backend
- React + TypeScript frontend
- SQLite migrations
- pytest + coverage
- ESLint + Prettier + TypeScript checks
- Vitest unit tests
- Playwright E2E
- dependency audits
- CodeQL
- pull-request CI gates

## Public-edition limitations

This showcase is not a drop-in mirror of the private production repository. Sensitive operational surfaces, private data, runtime state and credentials are deliberately excluded.
