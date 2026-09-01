# Changelog

All notable project changes are recorded here. The project follows a lightweight
Keep-a-Changelog style and uses semantic version tags when a stable milestone is
ready to demonstrate.

## Unreleased

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
- branch-protection guidance now includes code-owner review, conversation
  resolution, admin non-bypass, E2E, and security checks

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
