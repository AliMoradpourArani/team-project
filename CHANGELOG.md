# Changelog

All notable project changes are recorded here. The project follows a lightweight Keep-a-Changelog style and uses semantic version tags when a stable milestone is ready to demonstrate.

## Unreleased

### Added

- read-only professor GitHub integration for the configured repository
- explicit optional `github_username` mapping in tracked user data
- per-member recent commit, pull-request, merged-PR, and open-PR metrics
- recent GitHub commit/pull-request contribution timeline
- repository status summary with default branch, last push, and open PR count
- short-lived in-process GitHub response cache and offline-safe unavailable state
- deterministic GitHub aggregation tests that do not require network access
- `docs/github-integration.md` and ADR 0003 for the external read-model boundary
- local student/professor authentication with Argon2 password hashing
- revocable server-side sessions stored in runtime SQLite
- HttpOnly SameSite session cookie and per-session CSRF protection
- local account bootstrap/rotation CLI
- student ownership authorization for users, activities, and projects
- professor-wide read-only dashboard with team totals, member progress, recent activity, and member drill-down
- persistent Docker runtime volume for private auth/database state
- Phase 3 student/professor Playwright flows
- authentication architecture documentation and ADR 0002

### Changed

- user runtime schema now carries optional GitHub identity mapping via append-only migration 006
- `httpx` is a runtime dependency because the backend owns external GitHub reads
- Docker forwards GitHub configuration and an optional runtime-only token to the backend
- browser E2E disables GitHub network access so CI remains deterministic
- protected API collections require authentication and filter by role
- professor access is explicitly read-only
- CORS allows credentials only for configured explicit origins
- CODEOWNERS covers authentication, professor dashboard, and GitHub integration paths

## 0.2.5 - 2026-09-01

### Added

- CODEOWNERS coverage for high-risk platform paths
- Playwright browser E2E flow for activity create/view/delete
- backend test coverage gate
- dependency review, `pip-audit`, `npm audit`, and CodeQL security workflows
- weekly Dependabot updates for Python, frontend, E2E, and GitHub Actions
- secure AI pull-request reviewer that reads diff text without executing PR code
- structured request logging and `X-Request-ID` correlation
- frontend render error boundary
- structured bug/feature issue templates
- architecture decision record process
- repository security policy and stronger PR checklist

### Changed

- GitHub Actions upgraded to Node 24-compatible major versions
- branch-protection guidance includes code-owner review, conversation resolution, admin non-bypass, E2E, and security checks

## 0.2.0 - 2026-09-01

### Added

- activity create/edit/delete backed by Git-tracked JSON
- per-user calendar and timeline
- user dashboard statistics and project summary
- source-data reconciliation safeguards and regression tests
- Docker bind mount for Git-visible activity writes

## 0.1.0 - 2026-08-31

### Added

- FastAPI + React/TypeScript modular-monolith foundation
- reproducible SQLite migrations and JSON source-data model
- Docker/native setup scripts, CI, contribution rules, and project contracts
