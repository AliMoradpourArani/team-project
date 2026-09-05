# Controlled Project Runner

Phase 5 connects each member's specialized project to the shared platform without turning the backend into an arbitrary shell executor.

## Goals

- surface executable project integration status in student/professor dashboards
- keep project ownership tied to authoritative `data/projects/*.json`
- validate Git-tracked project manifests before execution
- support a deliberately narrow runner allowlist
- make execution switchable off at runtime via a kill switch
- return bounded, structured execution results to the UI

## Current runner allowlist

Only this contract is supported:

```text
project_type = cli
runner       = python-script-v1
entry_point  = relative .py file
```

The backend derives the command itself:

```text
<backend-python> -B <entry_point>
```

It never evaluates `run`, `build`, `command`, or another manifest-provided command string.

## API

Authenticated users see only projects already visible to their role:

```text
GET /api/projects/integrations
```

Students can execute only their own visible projects. Professors can execute reviewed projects while inspecting a member dashboard:

```text
POST /api/projects/{project_id}/run
```

The POST endpoint requires the normal session and CSRF token.

A run response contains:

```json
{
  "projectId": "team-foundation",
  "runner": "python-script-v1",
  "exitCode": 0,
  "timedOut": false,
  "durationMs": 31,
  "stdout": "Team Platform example project is running.\n",
  "stderr": "",
  "outputTruncated": false
}
```

## Runtime configuration

Execution is **enabled by default** for local development so the code-editor
**Run** works out of the box. `PROJECT_RUNNER_ENABLED=false` is the explicit
kill switch and should be set for locked-down/containerized deployments:

```text
PROJECT_RUNNER_ENABLED=true
PROJECT_RUNNER_TIMEOUT_SECONDS=5
PROJECT_RUNNER_OUTPUT_LIMIT=16000
```

Disable process execution for a hardened deployment:

```bash
export PROJECT_RUNNER_ENABLED=false
```

For Docker, keep execution disarmed unless you explicitly opt in:

```bash
PROJECT_RUNNER_ENABLED=true docker compose up -d --build
```

Compose mounts `./projects` at `/app/projects` as read-only.

## Security boundary

The runner reduces accidental command-injection risk, but it is **not a sandbox**.

Controls implemented:

- no shell interpretation (`shell=False`)
- no manifest-provided command execution
- allowlisted runner type
- relative-path validation and repository confinement
- symlink rejection for executable paths
- authoritative owner/id matching
- CSRF protection on execution
- student ownership authorization
- explicit runtime feature flag
- timeout
- bounded stdout/stderr returned to the client
- minimal child-process environment
- read-only project source mount in Docker

Controls **not** provided:

- network namespace isolation
- filesystem sandboxing for the native backend process
- syscall filtering
- container-per-run isolation
- protection from malicious code intentionally committed to the repository

Therefore, only run code that has gone through the repository's normal PR, CI, and review workflow. If the project later needs to execute genuinely untrusted submissions, replace this runner with a dedicated isolated execution service/container boundary.

## Adding a member project

1. Add authoritative metadata under `data/projects/<project_id>.json`.
2. Add source under `projects/<owner>/<project-directory>/`.
3. Add a valid `project.json` using the contract in `docs/project-contract.md`.
4. Make sure the manifest `id` equals the authoritative project id and `owner_id` matches the project owner.
5. Submit the code through a feature branch and PR.
6. Let CI/security checks pass and review the executable code.
7. Execution is enabled by default locally so the demo can run; set `PROJECT_RUNNER_ENABLED=false` for a hardened deployment.

The UI will show projects as `ready`, `not-integrated`, or `invalid`, making integration problems visible instead of silently guessing how to run a project.
