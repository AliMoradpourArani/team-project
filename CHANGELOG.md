# Changelog

All notable project changes are recorded here. The project follows a lightweight Keep-a-Changelog style and uses semantic version tags when a stable milestone is ready to demonstrate.

## Unreleased

### Added

- Phase 11 Final Delivery Preflight shared across professor API, UI, local CLI, CI smoke checks, and release creation
- global final-delivery gates for tracked projects, runtime professor/student accounts, complete Phase 10 integration, frozen submissions, and final approval ordering
- per-project final-delivery gates for integration readiness, frozen submission, professor approval, and approval-after-freeze sequencing
- professor-only `GET /api/professor/preflight` readiness report with blocker counts, remediation, and release-candidate readiness
- `make delivery-preflight` strict local final gate plus `make delivery-preflight-report` diagnostic mode
- server-side release-candidate guard that refuses `POST /api/professor/releases` while preflight is blocked
- final approval sequencing invariant requiring the professor approval timestamp to be at or after the latest frozen submission timestamp
- professor Final Delivery Control UI with global gates, per-project blockers, exact remediation, and release-candidate controls
- CI report-only preflight smoke check against a fresh runtime database
- `docs/final-delivery-preflight.md` documenting the final order: integrate → freeze → approve → preflight → release candidate
- Phase 11 backend/frontend tests covering professor-only access, blocked-state reporting, release bypass prevention, and approval sequencing
- Phase 10 shared Member Project Onboarding & Integration Gates model for API, UI, local CLI, and CI
- six blocking readiness gates for tracked metadata, manifest, owner mapping, paths, typed demo contract, and README
- authenticated onboarding endpoints for visible project lists and per-project readiness
- `make project-check PROJECT_ID=<id>` local teammate pre-PR validation with actionable remediation and nonzero exit until ready
- repository-wide `python -m backend.project_check` CI validation that allows pending placeholders but rejects invalid attempted integrations
- optional `--strict` project check for the final team-wide readiness freeze
- generic frontend onboarding panel on every project detail page with expected paths, gate status, remediation, supported contracts, and the exact local command
- `docs/member-project-onboarding.md` documenting teammate handoff, readiness states, CI behavior, and the Phase 9 boundary
- Phase 10 backend/frontend tests covering ready, pending, invalid, ownership, and submission-readiness alignment
- Phase 9 immutable, versioned project submissions with canonical SHA-256 snapshot fingerprints
- professor-controlled submission window with optional timezone-aware deadline
- student-owned frozen source snapshots with per-file SHA-256, bounded Base64 content, integration health, and review-at-submit metadata
- professor Submission & Release control center with submitted/pending/approved readiness counts
- immutable team release manifests pinning project submission versions/digests and approved review state
- runtime-only `submission_settings`, `project_submissions`, and `submission_releases` state via append-only migration 009
- snapshot safety limits plus rejection of symlinks and likely secret files such as `.env`, private keys, `.pem`, `.key`, `.p12`, and `.pfx`
- Phase 9 backend/frontend tests and Playwright frozen-submission delivery flow
- `docs/submission-release.md` documenting immutable delivery, authorization, safety bounds, and release gates
- Phase 8 professor Project Review & Evaluation workflow
- runtime-only `project_reviews` SQLite state with append-only migration 008
- fixed 100-point rubric for functionality, code quality, documentation, integration, and contribution
- professor review states: in-review, changes-requested, and approved; missing review means pending
- professor project review queue with status counts and direct project links
- project-level professor review create/update/reset endpoints protected by professor role + CSRF
- student read-only visibility into feedback and rubric for their own project
- frontend review editor, read-only feedback panel, queue UI, unit tests, and Playwright review flow
- `docs/project-review-evaluation.md` documenting the runtime-only evaluation boundary
- Phase 7 typed CLI, static-web, and OpenAPI demo contracts
- sandboxed static HTML project preview with restrictive CSP
- validated bounded OpenAPI 3.x JSON preview without starting an API server
- Phase 6 generic member-project detail pages at `/projects/<project_id>`
- project integration health checklist for tracked metadata, manifest, owner mapping, paths, runner contract, and README
- safe plain-text project README preview in the shared UI
- runtime-only SQLite project demo history with bounded stdout/stderr previews
- integration onboarding checklist in `projects/README.md`
- `docs/member-project-integration.md` for teammate project handoff and review workflow
- Phase 5 controlled Project Integration / Runner for reviewed member projects
- validated `project.json` execution contract with authoritative project/owner matching
- allowlisted `python-script-v1` runner that derives argv server-side and never executes manifest shell strings
- professor/student project integration status in the dashboard (`ready`, `not-integrated`, `invalid`)
- structured project run results with exit status, duration, timeout state, stdout/stderr, and response truncation metadata
- opt-in runner configuration with timeout/output limits and Docker read-only project source mount
- project runner backend/frontend tests, security documentation, and ADR 0004
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

- API version is now `0.11.0`
- release candidate creation now re-runs Phase 11 preflight server-side and cannot be bypassed through direct HTTP calls
- a final professor approval only covers a frozen submission when the approval is recorded after that submission
- normal CI exercises final-delivery preflight in report-only mode while the strict command remains reserved for the real final checkpoint
- Phase 9 submission status now reports `canSubmit=false` until Phase 10 onboarding gates are ready, while the actual submission mutation still revalidates server-side
- project detail pages now show the same readiness model and remediation used by local project checks and CI
- CODEOWNERS now protects onboarding and final-delivery schemas/services/CLI/UI/docs alongside existing runner, review, and submission boundaries
- professor access remains read-only for shared student data; Phase 9 adds writes only to separate runtime submission settings and immutable release manifests
- project detail pages now surface immutable submission state beside integration, demo, and professor review information
- CODEOWNERS now protects submission/release backend services and frontend controls as high-risk Core paths
- professor access remains read-only for shared student data, while Phase 8 permits writes only to separate runtime evaluation state
- project detail pages now surface professor evaluation in the same generic route for every member project
- project cards now link to generic data-driven detail pages instead of requiring Core changes per member project
- demo executions invoked through the API are recorded in runtime history without modifying Git-tracked project data
- the reference `team-foundation` project now includes the README required by the Phase 6 health checklist
- executable and evaluation-sensitive paths are CODEOWNERS-protected
- the example project manifest now links to authoritative project id `team-foundation` and uses `runner: python-script-v1`
- Docker mounts `./projects` read-only into the backend container
- user runtime schema now carries optional GitHub identity mapping via append-only migration 006
- `httpx` is a runtime dependency because the backend owns external GitHub reads
- Docker forwards GitHub configuration and an optional runtime-only token to the backend
- browser E2E disables GitHub network access so CI remains deterministic
- protected API collections require authentication and filter by role
- professor access is explicitly read-only for shared application data
- CORS allows credentials only for configured explicit origins
- CODEOWNERS covers authentication, professor dashboard, GitHub integration, project runner, project evaluation, submission/release, onboarding, and final-delivery paths

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
