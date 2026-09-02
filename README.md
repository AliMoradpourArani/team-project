# Team Project

A local-first university team platform for recording daily work, presenting individual progress, integrating reviewed member projects, and giving the professor a clear team view.

The application is one shared platform, not one duplicated website per student. User-specific behavior is driven by authenticated identity, `user_id`, tracked data, and typed project manifests.

## Current status

| Phase | Status | What it adds |
| --- | --- | --- |
| Phase 1 | ✅ Complete | FastAPI/React/SQLite foundation, migrations, reproducible setup, Git workflow |
| Phase 2 | ✅ Complete | Activity CRUD, calendar, timeline, personal dashboard, Git-tracked activity writes |
| Phase 2.5 | ✅ Complete | E2E, coverage gates, security scanning, CODEOWNERS, Dependabot, observability, optional AI PR review |
| Phase 3 | ✅ Complete | Local authentication, student/professor authorization, CSRF protection, professor dashboard |
| Phase 4 | ✅ Complete | Read-only GitHub integration, repository status, commit/PR metrics, contribution timeline |
| Phase 5 | ✅ Complete | Validated controlled Project Integration / Runner |
| Phase 6 | ✅ Complete | Generic member-project detail pages, health checks, safe README view, runtime demo history, integration checklist |
| Phase 7 | ✅ Complete | Typed CLI/static-web/API demos, sandboxed static preview, validated OpenAPI preview |
| Phase 8 | ✅ Complete | Professor review queue, fixed 100-point rubric, runtime-only feedback/evaluation, student read-only feedback |
| Phase 9 | ✅ Complete | Immutable versioned submissions, professor submission controls, SHA-256 source snapshots, frozen team release manifests |
| Phase 10 | ✅ Complete | Shared member-project onboarding gates across API/UI/CLI/CI with `ready`, `pending`, and `invalid` states |
| Phase 11 | ✅ Complete | Final-delivery preflight, approval-after-freeze sequencing, release-candidate guard, strict local final check |

## What the platform does

### Student

Each student signs in to one protected workspace and can:

- view their profile and dashboard,
- create/edit/complete/delete their own activities,
- browse work through calendar and timeline views,
- inspect their own projects and integration status,
- open a generic project page at `/projects/<project_id>`,
- see project health checks, onboarding gates, and README documentation,
- run a reviewed Python CLI demo when execution is explicitly enabled,
- preview static-web projects without starting a process,
- inspect validated OpenAPI 3.x contracts for API projects,
- see recent local history for executed demos,
- read professor review status, rubric score, and written feedback for their own project,
- freeze immutable versioned submissions of their own integrated project source.

Students cannot access another student's protected data, project, review, or submission flow by changing a URL or API parameter.

### Professor

The professor can:

- view team progress and recent activities,
- drill into member dashboards,
- inspect all member projects and integration health,
- view repository/GitHub contribution signals,
- open every project's generic detail page,
- preview static/OpenAPI demos safely,
- run reviewed executable demos when local execution is enabled,
- view a project review queue across the team,
- create/update/reset runtime-only project evaluations with a fixed 100-point rubric,
- leave written feedback visible to the owning student,
- open/close the project submission window and configure a deadline,
- inspect immutable submission history and frozen source fingerprints,
- run the shared Phase 11 final-delivery preflight,
- freeze an immutable team release candidate only after every blocking final-delivery gate passes.

The professor remains read-only for **shared student source data**. Professor writes are limited to separate private/runtime evaluation, submission-control, and immutable release state in SQLite.

## Architecture

The application is a **modular monolith**.

```text
                         Team Project
                              │
              ┌───────────────┴───────────────┐
              │                               │
          React/Vite                       FastAPI
          TypeScript                       Backend
              │                               │
              └────────────── API ────────────┘
                                              │
          ┌───────────────────────┬───────────┴─────────────┐
          │                       │                         │
   Git-tracked JSON            SQLite                  GitHub API
   shared source data       runtime/private state     read-only data
          │                       │
          │                       ├── auth/session state
          │                       ├── executed demo history
          │                       ├── professor project reviews
          │                       └── submissions / releases
          │
          └── projects/<owner>/<project>/
                     │
                     ├── project.json
                     ├── README.md
                     └── validated typed entry point
                              │
                 ┌────────────┼────────────┐
                 │            │            │
             Python CLI   Static HTML   OpenAPI JSON
              execute       preview        preview
```

Core technology:

- **Frontend:** React + Vite + TypeScript
- **Backend:** FastAPI + Pydantic
- **Database:** SQLite with ordered append-only SQL migrations
- **Shared source:** Git-tracked JSON under `data/`
- **Authentication:** Argon2 + server-side sessions + CSRF
- **GitHub integration:** read-only API client with short cache
- **Project integration:** validated typed manifests + generic detail read model
- **Project demos:** allowlisted execution/preview contracts
- **Evaluation:** professor-owned runtime-only rubric state in SQLite
- **Delivery:** immutable source submissions, frozen release manifests, computed final-delivery preflight
- **Testing:** pytest, Vitest, Playwright
- **Quality/security:** Ruff, ESLint, Prettier, TypeScript, dependency audits, CodeQL

## Source of truth

Shared data stays Git-visible:

```text
data/
├── users/<user_id>.json
├── activities/<user_id>/<date>.json
└── projects/<project_id>.json
```

SQLite is derived/runtime state. It also stores private local authentication state, executed project demo history, professor evaluations, immutable project submissions, submission settings, and frozen team releases. Phase 11 preflight is computed on demand and is not persisted as another source of truth.

```text
Git-tracked JSON
      │
      ▼
   db-sync
      │
      ▼
    SQLite ───── auth / history / reviews / submissions / releases
      │
      ▼
  FastAPI API
      │
      ▼
   React UI
```

Passwords, password hashes, sessions, API tokens, and other secrets are never stored in Git-tracked user JSON. Professor reviews and delivery/runtime state are also intentionally not written into student Git-tracked data.

## Repository structure

```text
team-project/
├── frontend/                  # React/Vite/TypeScript UI
├── backend/
│   ├── auth/                  # Local account bootstrap
│   ├── app/                   # FastAPI routes/dependencies
│   ├── schemas/               # API/source/auth/integration/review/delivery contracts
│   ├── services/              # Business logic and integrations
│   └── database/              # SQLite migrations/init/sync
├── data/                      # Authoritative shared metadata
├── projects/<owner>/<name>/   # Reviewed member project source
├── e2e/                       # Playwright flows
├── tests/                     # Backend tests
├── docs/
├── .github/
├── CHANGELOG.md
├── SECURITY.md
├── docker-compose.yml
└── Makefile
```

## Quick start

Prerequisites: Git, Python 3.11+, Node.js 20+, npm. Docker is optional.

```bash
git clone https://github.com/HoosseinRahimi/team-project.git
cd team-project
make setup
make db-init
make db-sync
make auth-bootstrap
```

Run `make auth-bootstrap` once per student and once for the professor. A student account must link to an existing tracked `user_id`.

Backend:

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload
```

Frontend:

```bash
npm run dev --prefix frontend
```

Open:

- App: <http://localhost:5173>
- API: <http://localhost:8000>
- FastAPI docs: <http://localhost:8000/docs>

### Docker

```bash
docker compose up -d --build
docker compose exec backend python -m backend.auth.bootstrap
```

Docker mounts:

```text
./data        -> /app/data       (read/write, Git-visible shared data)
./projects    -> /app/projects   (read-only reviewed project source)
team-runtime  -> /app/runtime    (private SQLite/auth/history/review/submission/release state)
```

## Authentication and authorization

### Student

- linked to exactly one tracked user,
- reads only their own protected user/activity/project data,
- modifies only their own activities,
- can inspect/run/preview only their own visible projects,
- can read only the professor review attached to their own visible project,
- can submit only their own integration-ready project,
- cannot mutate project review, submission settings, or release state.

### Professor

- views all members and project/activity summaries,
- drills into member/project details,
- views GitHub contribution analytics,
- can inspect all typed project previews,
- can invoke reviewed executable demos when execution is enabled,
- can write only to runtime project-evaluation/submission-control/release state,
- can view the final-delivery preflight across all tracked projects,
- does not receive normal shared-data write access.

Authentication endpoints:

```text
POST /api/auth/login
GET  /api/auth/me
POST /api/auth/logout
```

Unsafe authenticated requests require `X-CSRF-Token`.

## Activities

```text
GET    /api/activities
POST   /api/activities
PUT    /api/activities/{activity_id}
DELETE /api/activities/{activity_id}
```

Activity writes update authoritative Git-tracked JSON and then reconcile SQLite.

## GitHub integration

Optional GitHub identity is explicit in tracked user data:

```json
{
  "id": "hossein",
  "display_name": "Hossein",
  "role": "Developer",
  "github_username": "HoosseinRahimi"
}
```

The application never guesses GitHub accounts from names or emails.

Runtime configuration:

```text
GITHUB_INTEGRATION_ENABLED=true
GITHUB_REPOSITORY=HoosseinRahimi/team-project
GITHUB_CACHE_TTL_SECONDS=60
GITHUB_API_TIMEOUT_SECONDS=5
```

A runtime-only read token may be supplied as `GITHUB_TOKEN`. Never commit it.

## Member Project Integration

A member project has two linked pieces:

1. authoritative metadata: `data/projects/<project_id>.json`
2. reviewed project source: `projects/<owner>/<project-directory>/`

Required source layout:

```text
projects/<owner>/<project-directory>/
├── project.json
├── README.md
└── <typed-entry-point>
```

A normal project automatically uses the shared routes:

```text
/users/<user_id>
└── Projects
     └── /projects/<project_id>
```

Do not create member-specific Core routes or components.

### Phase 7 typed demo contracts

Only these `project_type` / `runner` pairs are valid:

| Project type | Runner | Entry point | Demo mode | Starts a project process? |
| --- | --- | --- | --- | --- |
| `cli` | `python-script-v1` | `.py` | execute | yes, opt-in |
| `static-web` | `static-site-v1` | `.html` / `.htm` | preview | no |
| `api` | `openapi-json-v1` | `.json` | preview | no |

Mismatched type/runner pairs are rejected by manifest validation.

#### Python CLI

```json
{
  "id": "example-cli",
  "name": "Example CLI",
  "owner_id": "student-id",
  "description": "Reviewed Python demo.",
  "technology": ["python"],
  "project_type": "cli",
  "runner": "python-script-v1",
  "entry_point": "main.py",
  "repository_path": "projects/student-id/example-cli"
}
```

This remains the only contract that starts a local project process.

#### Static web preview

```json
{
  "id": "example-web",
  "name": "Example Static Site",
  "owner_id": "student-id",
  "description": "Self-contained static frontend demo.",
  "technology": ["html", "css"],
  "project_type": "static-web",
  "runner": "static-site-v1",
  "entry_point": "index.html",
  "repository_path": "projects/student-id/example-web"
}
```

The backend reads bounded UTF-8 HTML. The frontend renders it in an iframe with an empty `sandbox` plus a restrictive CSP. Scripts, forms, network connections, nested frames, base URL changes, and navigation are not granted by the preview policy.

#### OpenAPI preview

```json
{
  "id": "example-api",
  "name": "Example API",
  "owner_id": "student-id",
  "description": "API contract demo.",
  "technology": ["openapi"],
  "project_type": "api",
  "runner": "openapi-json-v1",
  "entry_point": "openapi.json",
  "repository_path": "projects/student-id/example-api"
}
```

The backend requires valid OpenAPI 3.x JSON with a top-level `paths` object, normalizes it, applies size limits, and returns it as a text preview. It does **not** start an API server.

### Project detail page

`/projects/<project_id>` exposes:

- authoritative project metadata,
- integration state,
- Phase 10 onboarding readiness and remediation,
- independent health checks,
- safe plain-text README view,
- typed demo contract and mode,
- sandboxed static preview when applicable,
- validated OpenAPI preview when applicable,
- controlled CLI demo action when applicable,
- recent local history for executed demos,
- professor evaluation and feedback when available,
- immutable submission status and history.

Project endpoints:

```text
GET    /api/projects
GET    /api/projects/integrations
GET    /api/projects/onboarding
GET    /api/projects/{project_id}/detail
GET    /api/projects/{project_id}/onboarding
POST   /api/projects/{project_id}/run
GET    /api/projects/{project_id}/review
PUT    /api/projects/{project_id}/review      # professor + CSRF
DELETE /api/projects/{project_id}/review      # professor + CSRF
GET    /api/projects/{project_id}/submission
POST   /api/projects/{project_id}/submit      # owning student + CSRF
```

Preview-only projects cannot use the process runner. Demo history is stored only in runtime SQLite and is never written into Git-tracked project data or source.

### Runner safety boundary

Execution is disabled by default:

```text
PROJECT_RUNNER_ENABLED=false
PROJECT_RUNNER_TIMEOUT_SECONDS=5
PROJECT_RUNNER_OUTPUT_LIMIT=16000
```

After executable Python code passes normal PR/CI/review:

```bash
export PROJECT_RUNNER_ENABLED=true
```

For `python-script-v1`, the backend derives argv, uses `shell=False`, validates ownership/paths, rejects free-form manifest commands, and bounds runtime/output. Project source is mounted read-only in Docker.

The Python runner is **not a sandbox for hostile code**. Only reviewed repository code should be enabled.

Static/OpenAPI contracts deliberately avoid starting project processes. A future untrusted web/API execution feature should use a separate isolated container/sandbox service rather than widening backend privileges.

## Phase 8 Project Review & Evaluation

The professor dashboard includes a review queue for all tracked projects. A project with no review is `pending`; saved reviews can be `in-review`, `changes-requested`, or `approved`.

The fixed rubric totals 100 points:

| Criterion | Max |
| --- | ---: |
| Functionality | 30 |
| Code quality | 20 |
| Documentation | 15 |
| Integration | 20 |
| Contribution | 15 |
| **Total** | **100** |

Professor review state is stored only in runtime SQLite table `project_reviews`. It does not modify `data/`, project source, activities, or Git history.

Professor queue endpoint:

```text
GET /api/professor/reviews
```

Students see their own review read-only on the same generic project detail page. The backend, not frontend routing, enforces review ownership and professor-only mutations.

See [Project Review & Evaluation](docs/project-review-evaluation.md) for the full boundary and authorization model.

## Phase 9 Immutable Submission & Release

Students freeze versioned snapshots of their own final integrated project source. Every snapshot has a canonical SHA-256 fingerprint and bounded source metadata. Previous versions remain immutable even if Git-tracked source changes later.

The professor controls the submission window and can inspect submission history. Team releases are immutable manifests that pin the selected frozen project submissions.

Important delivery endpoints:

```text
GET  /api/professor/submissions
PUT  /api/professor/submission-settings     # professor + CSRF
GET  /api/professor/releases
POST /api/professor/releases                # professor + CSRF + Phase 11 preflight
GET  /api/professor/releases/{release_id}
```

Snapshot creation rejects unsafe inputs such as symlinks, likely secret files, and sources that exceed configured bounds.

See [Submission & Release](docs/submission-release.md) for the immutable delivery model.

## Phase 10 Member Project Onboarding

Every tracked member project uses one shared readiness model instead of member-specific integration code. The six blocking gates cover:

1. tracked project metadata,
2. manifest validity,
3. owner mapping,
4. repository path containment,
5. typed demo contract,
6. README availability.

Readiness states are `ready`, `pending`, and `invalid`.

Local validation for one project:

```bash
make project-check PROJECT_ID=team-foundation
```

Repository-wide normal validation allows not-yet-integrated placeholders to remain `pending`, but malformed attempted integrations become `invalid` and fail CI. The strict final form is:

```bash
.venv/bin/python -m backend.project_check --strict
```

See [Member Project Onboarding](docs/member-project-onboarding.md) for the complete handoff and gate behavior.

## Phase 11 Final Delivery Preflight

The final-delivery order is deliberately strict:

```text
integrate → freeze final source → professor approves after freeze → preflight → release candidate
```

The shared preflight checks global runtime readiness plus per-project integration, frozen submission, professor approval, and approval sequencing. If a student freezes a newer submission after an earlier approval, that older approval no longer covers the latest frozen version.

Professor endpoint:

```text
GET /api/professor/preflight
```

Local diagnostics:

```bash
make delivery-preflight-report
```

Strict final gate:

```bash
make delivery-preflight
```

The strict command exits nonzero until the entire team is ready. Normal CI uses report-only mode so incomplete teammate placeholders do not make every development PR fail.

Release creation re-runs preflight server-side. Disabling the browser button is not the security boundary; a direct HTTP request also receives `409` while preflight is blocked.

See [Final Delivery Preflight](docs/final-delivery-preflight.md) for the complete release-candidate rules.

## Member integration checklist

Before a teammate opens a project PR:

```text
[ ] data/projects/<project_id>.json exists
[ ] owner_id is correct
[ ] project.json validates
[ ] project_type / runner pair is allowlisted
[ ] repository_path exactly matches the directory
[ ] README.md documents purpose/setup/input/output/demo
[ ] entry point exists inside the project
[ ] no secrets are committed
[ ] no run/build/command shell fields are present
[ ] make project-check PROJECT_ID=<project_id> reports READY
[ ] tests pass
[ ] CI + security checks are green
```

See [projects/README.md](projects/README.md) for the handoff contract.

## Database commands

```bash
make db-init
make db-sync
make db-reset
```

Merged migrations are append-only. Never rewrite a migration already on `main`.

## Testing and quality gates

```bash
make test
```

CI covers:

- conflict-marker detection,
- backend Ruff/tests/coverage + fresh DB sync,
- Phase 10 repository-wide onboarding validation,
- Phase 11 report-only final-delivery preflight smoke test,
- frontend ESLint/Prettier/TypeScript/unit/build,
- Playwright Chromium E2E including auth, review, frozen submission, and final-preflight behavior,
- Python/npm dependency audits,
- CodeQL for Python and JavaScript/TypeScript.

Executable, evaluation-sensitive, onboarding, submission, and final-delivery paths remain CODEOWNERS-protected.

## Git workflow

`main` must remain runnable for the professor.

```text
main
  └── feature/fix/docs branch
          ↓
        commits
          ↓
           PR
          ↓
      CI + review
          ↓
      squash merge
          ↓
         main
```

Rules:

- no normal direct development on `main`,
- resolve conflicts on the feature branch,
- no force-push to `main`,
- prefer focused PRs and squash merge,
- executable project code must pass review/CI before runner enablement.

## Documentation

- [Architecture](docs/architecture.md)
- [Authentication](docs/authentication.md)
- [GitHub integration](docs/github-integration.md)
- [Project contract](docs/project-contract.md)
- [Project runner](docs/project-runner.md)
- [Member project integration](docs/member-project-integration.md)
- [Rich project demos](docs/rich-project-demos.md)
- [Project review & evaluation](docs/project-review-evaluation.md)
- [Submission & release](docs/submission-release.md)
- [Member project onboarding](docs/member-project-onboarding.md)
- [Final delivery preflight](docs/final-delivery-preflight.md)
- [Git workflow](docs/git-workflow.md)
- [Database rules](docs/database-rules.md)
- [Engineering quality](docs/engineering-quality.md)
- [Architecture decisions](docs/adr/)
- [Contributing](CONTRIBUTING.md)
- [Security](SECURITY.md)
- [Changelog](CHANGELOG.md)

## API conventions

- prefix application routes with `/api/`,
- use typed Pydantic request/response contracts,
- unknown resources -> `404`, malformed input -> `422`, unauthenticated -> `401`, forbidden -> `403`,
- never trust a frontend-provided user id as authorization proof,
- keep Git-tracked JSON authoritative for shared team data,
- keep credentials/sessions/secrets/runtime history/reviews/submissions/releases outside Git,
- compute final-delivery readiness from existing authoritative/runtime state instead of persisting a second readiness source,
- keep external integrations isolated/read-only where possible,
- never introduce arbitrary shell execution through project manifests.