# Project and data contract

## Git-tracked data files (`data/`)

The `data/` directory is the **authoritative shared source** for team information. One file per logical unit keeps merges conflict-friendly.

All files: UTF-8, 2-space indent, newline at end, no volatile generated fields.

### Users — `data/users/<user_id>.json`

```json
{
  "id": "hossein",
  "display_name": "Hossein",
  "role": "Developer",
  "github_username": "HoosseinRahimi"
}
```

The file name must match `id`.

`github_username` is optional. When present it is the explicit identity mapping used by the professor GitHub dashboard. Never infer a teammate's GitHub account from their display name, commit author name, or email address. Members without a mapping remain visible as `not linked`.

### Activities — `data/activities/<user_id>/<YYYY-MM-DD>.json`

```json
{
  "user_id": "hossein",
  "date": "2026-08-31",
  "activities": [
    {
      "id": "hossein-2026-08-31-init-repository",
      "title": "Initialize repository",
      "status": "completed",
      "project_id": "team-foundation"
    }
  ]
}
```

- `id` must be a **stable unique slug**, recommended `<user_id>-<date>-<short-description>`.
- `status` is one of `planned | in-progress | completed`.
- `project_id` may be `null` or the id of a project in `data/projects/`.

### Projects — `data/projects/<project_id>.json`

```json
{
  "id": "team-foundation",
  "owner_id": "hossein",
  "name": "Team Project Foundation",
  "description": "Initial repository and application foundation.",
  "technology": ["python"],
  "status": "active"
}
```

- `status` is one of `planned | active | completed | archived`.
- This file is authoritative project metadata. Executable integration details belong in the member project's `project.json` manifest under `projects/`.

### Validation rules

- **Identifiers (user/project/activity ids) are lowercase slugs:** `[a-z0-9][a-z0-9-]*`. They are used as file and directory names, so other characters are rejected.
- Dates are ISO 8601 calendar dates and must match their file name.
- `github_username`, when present, is 1-39 letters, digits, or hyphens and may not begin or end with a hyphen.
- All source-data files are validated with Pydantic models in `backend/schemas/source_data.py`. Malformed files fail loudly at load time with a message naming the offending file.

## Writing activities

Activity creation/editing preserves the Git-friendly model:

1. validate the activity against the schema,
2. write/update `data/activities/<user_id>/<date>.json`,
3. run the idempotent sync to update the runtime database.

Never store shared activities only in SQLite.

## GitHub identity mapping

The GitHub integration is a **read model**, not authoritative user data. `github_username` is the only accepted mapping between a team member and a GitHub account. The integration reads repository activity and associates it only with explicitly linked accounts.

Do not add access tokens, emails, API responses, contribution counts, commit SHAs, or other volatile GitHub data to `data/users/*.json`.

## Student projects (`projects/<owner>/<project>/`)

Each executable student project directory contains a validated `project.json` manifest. The manifest id must match a project id from `data/projects/`, and `owner_id` must match that authoritative project's owner.

Phase 5 supports one intentionally narrow runner contract:

```json
{
  "id": "team-foundation",
  "name": "Team Project Foundation",
  "owner_id": "hossein",
  "description": "Runnable demonstration for the shared team platform project.",
  "technology": ["python"],
  "project_type": "cli",
  "runner": "python-script-v1",
  "entry_point": "main.py",
  "repository_path": "projects/hossein/team-platform"
}
```

### Manifest rules

- `id` and `owner_id` are validated lowercase slugs.
- `repository_path` must be exactly `projects/<owner>/<project-directory>` and must match the manifest's real directory.
- `entry_point` must be a clean relative `.py` path inside the project directory.
- absolute paths, `..`, symlinked project directories, and symlinked entry-point paths are rejected.
- `project_type` is currently `cli` only.
- `runner` is currently `python-script-v1` only.
- duplicate manifest ids are invalid.
- unknown fields are rejected. In particular, `run`, `build`, `command`, and arbitrary shell strings are **not** accepted runner instructions.

### Execution rules

The backend never executes a manifest-provided shell string. For `python-script-v1` it derives one fixed argv template:

```text
<current-python> -B <validated-relative-entry-point>
```

Execution uses `shell=False`, an empty stdin, a restricted environment, a bounded timeout, and bounded response output. The project source is mounted read-only in Docker.

The runner is disabled by default and must be explicitly enabled at runtime after project code has passed normal PR review:

```text
PROJECT_RUNNER_ENABLED=true
```

This control is **not a security sandbox**. Reviewed Python code can still use the operating system and network permissions available to the backend process. Do not enable the runner for untrusted code. See [project-runner.md](project-runner.md) and [ADR 0004](adr/0004-controlled-project-runner.md).
