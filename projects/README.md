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
└── <entry-point>.py
```

Current runner contract:

```json
{
  "id": "example-project",
  "name": "Example Project",
  "owner_id": "student-id",
  "description": "Short project description.",
  "technology": ["python"],
  "project_type": "cli",
  "runner": "python-script-v1",
  "entry_point": "main.py",
  "repository_path": "projects/student-id/example-project"
}
```

The `id` must also exist in `data/projects/<id>.json`, and the authoritative `owner_id` must match.

## Integration checklist

Before opening a PR, verify:

- [ ] `data/projects/<project_id>.json` exists
- [ ] project `owner_id` is correct
- [ ] `project.json` validates
- [ ] `repository_path` exactly matches the real directory
- [ ] `README.md` explains purpose, setup, input, output, and demo usage
- [ ] entry point exists inside the project directory
- [ ] no secrets or credentials are committed
- [ ] no free-form `run`, `build`, `command`, or shell fields are added to the manifest
- [ ] local tests pass
- [ ] PR CI/security checks are green

After merge, the project detail page at `/projects/<project_id>` shows health checks, README, runner contract, and recent demo history.

The local runner is opt-in and is **not** a sandbox for hostile code. Only reviewed repository code should be executed.
