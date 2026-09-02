# Student projects

Each team member owns project source under:

```text
projects/<user_id>/<project-directory>/
```

The shared platform discovers projects through a strict `project.json` manifest. Do not add per-student routes or custom Core logic. A new member project should integrate through data + manifest only.

## Required files

```text
projects/<user_id>/<project-directory>/
├── project.json
├── README.md
└── <entry-point>
```

The `id` must also exist in `data/projects/<id>.json`, and the authoritative `owner_id` must match.

## Phase 10 onboarding gate

Before opening a PR, run the exact readiness check for your tracked project:

```bash
make project-check PROJECT_ID=<project_id>
```

Example:

```bash
make project-check PROJECT_ID=team-foundation
```

A single-project check exits nonzero until all six blocking gates pass. It prints the failed gate and the concrete remediation.

The six gates are:

1. tracked project metadata
2. valid typed `project.json`
3. owner mapping
4. repository/entry-point path containment
5. supported demo contract
6. readable `README.md`

Repository-wide CI also runs:

```bash
python -m backend.project_check
```

In repository-wide mode, a project that has not been integrated yet is `pending` and does not fail CI. An attempted but malformed integration is `invalid` and does fail CI. Once every team member has a real project, the Tech Lead can use `python -m backend.project_check --strict` to require every tracked project to be ready.

The generic project page shows the same gate model and remediation as the CLI. There is one source of readiness truth for student, professor, local checks, and CI.

## Supported Phase 7 demo contracts

### 1. Controlled Python CLI execution

```json
{
  "id": "example-cli",
  "name": "Example CLI",
  "owner_id": "student-id",
  "description": "Short project description.",
  "technology": ["python"],
  "project_type": "cli",
  "runner": "python-script-v1",
  "entry_point": "main.py",
  "repository_path": "projects/student-id/example-cli"
}
```

This is the only contract that starts a local process. Execution remains opt-in through `PROJECT_RUNNER_ENABLED=true`.

### 2. Sandboxed static web preview

```json
{
  "id": "example-web",
  "name": "Example Static Site",
  "owner_id": "student-id",
  "description": "Static frontend demo.",
  "technology": ["html", "css"],
  "project_type": "static-web",
  "runner": "static-site-v1",
  "entry_point": "index.html",
  "repository_path": "projects/student-id/example-web"
}
```

The platform reads the HTML as a bounded UTF-8 preview. The frontend renders it in a sandboxed iframe with a restrictive CSP. Scripts, forms, network connections, nested frames, and navigation are not granted by the preview policy.

### 3. OpenAPI JSON preview

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

The entry point must be valid OpenAPI 3.x JSON with a top-level `paths` object. The platform validates and normalizes the document before showing it as text. It does not start an API server.

## Integration checklist

Before opening a PR, verify:

- [ ] `data/projects/<project_id>.json` exists
- [ ] project `owner_id` is correct
- [ ] `project.json` validates
- [ ] the `project_type` / `runner` pair is one of the allowlisted contracts above
- [ ] `repository_path` exactly matches the real directory
- [ ] `README.md` explains purpose, setup, input, output, and demo usage
- [ ] entry point exists inside the project directory
- [ ] no secrets or credentials are committed
- [ ] no free-form `run`, `build`, `command`, or shell fields are added to the manifest
- [ ] `make project-check PROJECT_ID=<project_id>` reports `READY`
- [ ] local tests pass
- [ ] PR CI/security checks are green

After merge, the project detail page at `/projects/<project_id>` shows onboarding gates, health checks, README, the typed demo contract, safe preview when applicable, and runtime history for executed demos.

The local Python runner is opt-in and is **not** a sandbox for hostile code. Static/OpenAPI preview contracts intentionally do not start project processes. Phase 9 performs separate frozen-source safety checks when a student submits a project.
