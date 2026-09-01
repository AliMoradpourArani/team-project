# Member project integration

Phase 6 makes member projects data-driven. A teammate should be able to add a reviewed project without changing shared routing, dashboards, authentication, or runner internals.

## Integration flow

```text
data/projects/<project_id>.json
          │
          │ authoritative owner/name/status
          ▼
projects/<owner>/<project>/project.json
          │
          │ validated integration contract
          ▼
Project health checks
          │
          ├── manifest
          ├── owner mapping
          ├── repository / entry-point confinement
          ├── supported runner
          └── README
          │
          ▼
/projects/<project_id>
          │
          ├── project metadata
          ├── health checklist
          ├── README preview
          ├── controlled demo action
          └── recent runtime history
```

## Member responsibilities

Each member owns only their project directory and authoritative project metadata. Shared Core changes should not be necessary for a normal new project.

Required project directory:

```text
projects/<user_id>/<project-directory>/
├── project.json
├── README.md
└── main.py
```

The current executable contract remains intentionally narrow:

```text
project_type = cli
runner       = python-script-v1
```

See `projects/README.md` and `docs/project-contract.md` for the exact manifest rules.

## Project detail page

The canonical route is:

```text
/projects/<project_id>
```

Access is enforced by the backend:

- a student can read/run only their own project,
- a professor can inspect all team projects,
- changing the URL does not grant access to another student's project.

The README is returned as plain text and rendered as text, not injected HTML. This avoids treating repository documentation as trusted executable markup.

## Health checks

The detail endpoint reports independent checks instead of reducing every problem to one generic status. Current checks cover:

1. authoritative tracked project metadata,
2. valid `project.json`,
3. owner mapping,
4. repository and entry-point path confinement,
5. supported runner contract,
6. readable non-symlink `README.md`.

A project may still have runner status `ready` while a documentation health check is incomplete. This makes the runner boundary and project-review quality visible separately.

## Runtime history

Successful API execution attempts are recorded in runtime SQLite table `project_run_history`.

Stored fields are intentionally bounded:

- project id and runner,
- exit code / timeout state,
- duration,
- short stdout/stderr previews,
- truncation state,
- timestamp.

Run history is local runtime state. It is not written to Git-tracked JSON and does not modify member project source.

## Security boundary

Phase 6 does not broaden the runner introduced in Phase 5. The backend still derives argv, uses `shell=False`, validates paths, bounds execution, and rejects free-form shell fields.

The runner is still **not a hostile-code sandbox**. Only code that has passed the normal branch, PR, review, CI, and security workflow should be enabled locally.
