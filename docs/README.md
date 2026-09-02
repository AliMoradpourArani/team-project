# Documentation Index

Use this page as the map for the repository documentation.

## Start here

- [Main README](../README.md) - product overview, current capabilities, setup, configuration, and major workflows
- [Architecture](architecture.md) - state boundaries, modular-monolith structure, AI services, and external integration rules
- [AI Autonomy Platform](ai-autonomy-platform.md) - repository RAG, governed actions, progress inference, orchestration, automation, and production hardening
- [Security](../SECURITY.md) - repository, AI, secrets, runner, and external-action security boundaries
- [Contributing](../CONTRIBUTING.md) - branch, testing, migration, and AI/autonomy contribution rules

## Identity and data

- [Authentication](authentication.md) - student/professor authentication, sessions, CSRF, and authorization
- [Database Rules](database-rules.md) - Git-tracked source authority, SQLite runtime/private state, and migration rules
- [Project Contract](project-contract.md) - shared tracked project metadata contract

## GitHub and engineering

- [GitHub Integration](github-integration.md) - read-only contribution intelligence versus governed AI GitHub writes
- [Git Workflow](git-workflow.md) - branch and pull-request workflow
- [Engineering Quality](engineering-quality.md) - CI, tests, security automation, AI reviewer, and quality invariants
- [Branch Protection](branch-protection.md) - recommended `main` protection and required checks
- [Architecture Decisions](adr/) - accepted architectural decisions and rationale

## Member projects

- [Member Project Integration](member-project-integration.md) - adding reviewed project source to the shared platform
- [Member Project Onboarding](member-project-onboarding.md) - readiness gates and local/CI validation
- [Project Runner](project-runner.md) - controlled CLI execution contract and safety boundary
- [Rich Project Demos](rich-project-demos.md) - static/OpenAPI preview contracts

## Professor review and delivery

- [Project Review & Evaluation](project-review-evaluation.md) - professor review queue, rubric, feedback, and authorization
- [Submission & Release](submission-release.md) - immutable project snapshots and release manifests
- [Final Delivery Preflight](final-delivery-preflight.md) - final integration/freeze/approval/preflight/release sequence
- [Professor Handoff](professor-handoff.md) - operational handoff for demonstration/evaluation
- [Release Checklist](release-checklist.md) - final release verification
- [Release Packaging](release-packaging.md) - packaging/tagging workflow
- [Academic Submission](academic-submission.md) - academic delivery package workflow

## Change history

- [Changelog](../CHANGELOG.md) - notable platform changes

When a feature changes behavior, configuration, security boundaries, API contracts, or deployment requirements, update the closest relevant document and the main README/Changelog when the change is user-visible or platform-wide.
