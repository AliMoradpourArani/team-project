# Member Project Onboarding & Integration Gates

Phase 10 turns member-project integration from a checklist into one shared executable readiness model used by the backend API, frontend project page, local CLI, and CI.

## Goal

A teammate should be able to add a real project without editing shared React routes, FastAPI business logic, or member-specific Core code.

The normal handoff is data-driven:

```text
data/projects/<project_id>.json
projects/<owner_id>/<project-directory>/
├── project.json
├── README.md
└── <typed entry point>
```

The shared platform then discovers and validates the project automatically.

## The six blocking gates

Every tracked project receives the same six gates:

1. **Tracked project metadata** — `data/projects/<project_id>.json` exists and validates.
2. **Manifest** — `project.json` uses the strict typed schema. Unknown/free-form shell fields are rejected.
3. **Owner mapping** — manifest `owner_id`, authoritative project owner, and `projects/<owner_id>/` directory agree.
4. **Repository paths** — `repository_path` matches the real directory and the entry point stays inside it. Symlink escapes are rejected by the integration layer.
5. **Demo contract** — the project uses one of the allowlisted type/runner pairs and its entry point validates.
6. **README** — a readable UTF-8 `README.md` is present for reviewer/demo instructions.

A project is `ready` only when all six gates pass and the integration status is ready.

## Status model

### `ready`

All gates pass. The project is integration-ready for Phase 9 submission. Submission-window/deadline rules still apply, and Phase 9 performs its own final frozen-source safety checks.

### `pending`

The project is not integrated yet or has ordinary incomplete onboarding work such as a missing manifest or README. Pending placeholders do not make repository CI fail.

### `invalid`

An attempted integration violates the contract, for example a malformed manifest, forbidden free-form field, invalid type/runner pair, owner mismatch, traversal, or broken path. CI fails on invalid integrations because a broken integration must not be merged.

## Supported contracts

| Project type | Runner | Demo mode | Example entry point |
| --- | --- | --- | --- |
| `cli` | `python-script-v1` | execute | `main.py` |
| `static-web` | `static-site-v1` | preview | `index.html` |
| `api` | `openapi-json-v1` | preview | `openapi.json` |

The runner is derived from the typed contract. A member cannot add arbitrary `run`, `build`, `command`, or shell strings to `project.json`.

## Local workflow for a teammate

After adding metadata and project source:

```bash
cd ~/team-project
make setup
make project-check PROJECT_ID=<project_id>
```

Example:

```bash
make project-check PROJECT_ID=team-foundation
```

The command prints every gate, its PASS/FAIL state, and a concrete remediation. For a single `PROJECT_ID`, the command exits nonzero until the project is fully ready.

To scan the whole repository:

```bash
make project-check
```

Repository-wide mode allows `pending` projects but exits nonzero when an attempted integration is `invalid`. CI uses this mode.

For a final team-wide freeze check when every placeholder has been replaced by a real project, run:

```bash
.venv/bin/python -m backend.project_check --strict
```

Strict mode fails on both pending and invalid projects.

## API

Authenticated project visibility still applies.

```text
GET /api/projects/onboarding
GET /api/projects/{project_id}/onboarding
```

Students can only retrieve onboarding data for their own visible projects. Professors can inspect all member-project readiness read-only.

The per-project response contains:

- `status`
- `readyForSubmission`
- completed/total gate counts
- expected metadata and repository paths
- every gate with detail and remediation
- supported typed contracts
- the exact local `make project-check` command
- a computed next action

## UI

The generic `/projects/<project_id>` page displays a **Member project integration gates** panel. There are no member-specific pages or components.

Students see the exact remediation and local command they need before opening their PR. Professors see the same data as read-only readiness evidence.

## Phase 9 submission alignment

Before Phase 10, the submission-status endpoint only represented the professor submission window/deadline. A not-yet-integrated project could therefore show an enabled Submit button and only fail when the server attempted to freeze it.

Phase 10 aligns the status response with onboarding readiness:

```text
submission window open
        +
project onboarding ready
        =
canSubmit = true
```

The actual Submit operation still revalidates integration health and frozen-source safety server-side. The frontend is never the security boundary.

## CI behavior

The backend CI job runs:

```bash
python -m backend.project_check
```

This catches malformed attempted integrations without forcing unimplemented placeholder projects to become ready prematurely.

Normal CI and security checks remain required in addition to onboarding readiness.

## Teammate PR sequence

```text
create feature/<project-name>
        ↓
add/update data/projects/<id>.json
        ↓
add projects/<owner>/<project>/ source + manifest + README
        ↓
make project-check PROJECT_ID=<id>
        ↓
project shows READY 6/6
        ↓
run normal tests
        ↓
push branch + open PR
        ↓
CI/security/review
        ↓
squash merge
        ↓
professor review + Phase 9 submission
```

## Trust boundary

Onboarding readiness means the project satisfies the repository integration contract. It does not turn executable member code into untrusted-code-safe sandboxed code.

`python-script-v1` remains reviewed local repository code and execution is opt-in. Static/OpenAPI contracts remain preview-only. Phase 9 separately rejects likely secret files, symlinked source paths, and snapshot size-limit violations when freezing a submission.
