# Changelog

All notable project changes are recorded here. The project follows a lightweight Keep-a-Changelog style and uses semantic version tags when a stable milestone is ready to demonstrate.

## Unreleased

### Added

- persistent authenticated AI project threads, messages, project snapshots, and replanning
- streamed AI chat responses over Server-Sent Events on `POST /api/ai/threads/{threadId}/messages/stream` with typed `start`/`delta`/`error`/`done` events, incremental rendering in the AI agent panel, and the same prompt guard, ownership checks, persistence, and local fallback as the non-streaming endpoint
- provider-backed in-app AI chat with deterministic local fallback when `AI_API_KEY` is not configured
- structured project memory, decision history, and project-scoped memory search
- GitHub evidence links between activities and branches, commits, pull requests, or issues
- daily and weekly AI project briefs with progress, health, overdue work, GitHub signals, risks, and next actions
- bounded repository indexing and project-scoped lexical RAG through `/api/ai/repo/index` and `/api/ai/repo/query`
- diff-aware AI code review and log-grounded debugging endpoints
- evidence-backed progress inference with preview/apply modes and authoritative Git-tracked activity writes
- governed AI action engine using `propose -> approve -> execute`
- allowlisted AI actions for task creation, progress updates, decision recording, GitHub evidence linking, branch creation, issue creation, and pull-request creation
- server-only governed GitHub write configuration through `AI_GITHUB_TOKEN` and `AI_GITHUB_REPOSITORY`
- seven-specialist AI orchestration covering planning, project management, code review, debugging, progress, GitHub, and documentation
- project health scoring across delivery, code, security, tests, schedule, and documentation
- persistent AI risk notifications and recurring maintenance loop
- prompt-injection/secret-exfiltration guard, per-user AI rate limiting, bounded RAG/payload sizes, provider/GitHub timeouts, and AI action audit records
- AI autonomy database state for repository chunks, actions, memory events, health snapshots, and notifications
- student AI cockpit controls for health, weekly intelligence, repository indexing, GitHub progress synchronization, and multi-agent coordination
- Phase 11 Final Delivery Preflight, immutable submissions/releases, professor evaluation, typed project demos, onboarding gates, and earlier platform capabilities retained from the original delivery roadmap

### Changed

- API version is now `0.13.0`
- the platform positioning now reflects a project-management + GitHub-intelligence + governed-AI workspace instead of only the original university activity tracker
- GitHub architecture now distinguishes the read-only `GITHUB_*` integration from explicitly approved `AI_GITHUB_*` write actions
- Docker Compose now forwards AI provider, RAG, automation, and governed GitHub-write configuration to the backend
- `.env.example` documents the complete current AI/autonomy configuration surface without containing real secrets
- automatic evidence-backed progress mutation remains opt-in through `AI_AUTOMATION_APPLY_PROGRESS=false` by default
- applied AI task/progress mutations continue through the authoritative Git-tracked activity-write service rather than direct SQLite updates
- documentation now treats AI threads, memory, repository chunks, actions, notifications, and audit state as runtime/private SQLite state
- AI Review workflow remains non-blocking when its separate `OPENAI_API_KEY` Actions secret is unavailable; CI and Security remain authoritative required gates

### Security

- external AI/GitHub side effects require authenticated ownership checks and explicit action approval
- browser-provided/model-generated credentials are not accepted as GitHub write authority
- in-app `AI_API_KEY`, governed `AI_GITHUB_TOKEN`, read-only `GITHUB_TOKEN`, and Actions `OPENAI_API_KEY` are documented as separate credentials with separate responsibilities

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
