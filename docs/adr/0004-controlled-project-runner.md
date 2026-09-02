# ADR 0004: Controlled project runner

- Status: Accepted
- Date: 2026-09-02

## Context

The platform needs to present each member's specialized project and let the team/professor demonstrate reviewed projects locally. The original manifest draft included free-form `run` and `build` strings. Executing those strings would turn the backend into a shell gateway and make command injection, path traversal, and accidental host damage much easier.

At the same time, a full untrusted-code sandbox is outside the current university project's scope and would require a separate isolation boundary.

## Decision

Project execution is implemented as an opt-in, allowlisted runner service.

For Phase 5:

- authoritative project identity/ownership stays in `data/projects/*.json`
- executable metadata lives in `projects/<owner>/<project>/project.json`
- manifests are validated with `extra=forbid`
- free-form command fields are not part of the runner contract
- the only supported execution pair is `cli` + `python-script-v1`
- the backend derives argv itself and uses `shell=False`
- paths must stay inside the declared project directory and symlinked executable paths are rejected
- student execution is limited to the student's own visible projects
- professor execution is permitted for reviewed demos without changing shared project data
- POST execution requires CSRF protection
- execution is disabled by default with `PROJECT_RUNNER_ENABLED=false`
- timeout/output limits and a minimal child environment are applied
- Docker mounts the project source read-only

## Consequences

### Positive

- no arbitrary shell string is interpreted by the backend
- the same manifest contract works for native and Docker demonstrations
- invalid/not-integrated projects are visible in the UI
- ownership remains tied to the existing source-of-truth model
- new runner types can be added explicitly rather than accepting arbitrary commands

### Tradeoffs

- only Python CLI demos are supported initially
- reviewed Python code still runs with the operating-system permissions of the backend process
- this is not safe for hostile/untrusted submissions
- projects requiring services, browsers, GPUs, package installation, or network isolation need future dedicated runner types or a separate sandbox service

## Rejected alternatives

### Execute `run` with `shell=True`

Rejected because it makes the Git-tracked manifest an arbitrary command-execution interface.

### Split command text and run with `shell=False`

Still rejected as the primary contract because a manifest could select arbitrary executables/arguments. The backend should own the allowed command template.

### Docker socket from the backend

Rejected for this phase. Mounting the host Docker socket into the web backend would create a much larger privilege boundary than the problem requires.

### Claim the subprocess runner is a sandbox

Rejected. The documentation and UI explicitly state that execution is for reviewed repository code only.
