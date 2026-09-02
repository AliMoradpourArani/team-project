# Submission & Release System

Phase 9 adds a runtime-only final-delivery workflow without changing the ownership boundary of student source data.

## Goals

- let a student freeze an immutable version of their own integrated project,
- give the professor a submission window and optional deadline,
- preserve every submission version instead of overwriting history,
- make a frozen team release possible only after every tracked project is submitted and approved,
- keep student Git/source data read-only to professor controls.

## Submission window

The professor controls one runtime submission window:

- `isOpen`: manual open/closed switch,
- `deadlineAt`: optional timezone-aware ISO 8601 deadline,
- `acceptingSubmissions`: computed server-side from the switch and deadline.

Settings live in SQLite table `submission_settings`. They are not Git-tracked curriculum/source data.

## Frozen project submission

A student may submit only a project owned by their authenticated `user_id`. Submission requires:

1. the professor submission window is accepting submissions,
2. the project integration status is `ready`,
3. all integration health checks pass,
4. project source stays inside the reviewed `projects/` tree,
5. snapshot size/file-count limits are respected.

Each successful submission creates a new immutable row in `project_submissions`. Existing versions are never updated or deleted by the normal API.

### Snapshot contents

The runtime snapshot records:

- authoritative project metadata,
- validated integration contract,
- integration health results,
- professor review state at submission time, when present,
- bounded project source files including relative path, byte size, SHA-256 and Base64 content.

The canonical snapshot JSON receives its own SHA-256 `snapshotDigest`. Two identical submissions can therefore have different version numbers while retaining the same digest.

Generated/cache directories such as `.git`, `.venv`, `node_modules`, `__pycache__`, and `.pytest_cache` are excluded. Symlinked source paths are rejected.

Default safety bounds:

- at most 300 source files,
- at most 5 MB total source bytes,
- at most 2 MB for one source file.

These limits keep runtime SQLite snapshots bounded. They can be revisited later if member projects legitimately need larger binary assets.

## Professor submission dashboard

`GET /api/professor/submissions` returns:

- submission settings,
- total/submitted/pending project counts,
- approved-review count,
- latest frozen submission per project,
- current professor review per project,
- release readiness and a blocking reason.

Professor settings mutation:

```text
PUT /api/professor/submission-settings
```

This requires professor role plus CSRF.

## Frozen team release

A team release is an immutable manifest, not a mutation of student source.

Release creation requires every tracked project to have:

- at least one frozen submission,
- a current professor review with status `approved`.

The release manifest pins, for every project:

- project and owner id,
- frozen submission id/version/digest,
- submission timestamp,
- current approved review score/status/timestamp.

The canonical manifest receives its own SHA-256 `manifestDigest` and is persisted in `submission_releases`.

Endpoints:

```text
GET  /api/professor/releases
GET  /api/professor/releases/{release_id}
POST /api/professor/releases
```

Release creation requires professor role plus CSRF. Release labels are unique to avoid ambiguous frozen deliveries.

## Authorization boundary

### Student

- can read submission state only for visible/owned projects,
- can create a new frozen version only for their own project,
- cannot change submission settings,
- cannot create or inspect professor release manifests.

### Professor

- can inspect submission state for all tracked projects,
- can open/close the submission window and set a deadline,
- can create immutable release manifests after readiness gates pass,
- cannot create a student submission,
- cannot rewrite old project submissions,
- still cannot edit student Git-tracked project/activity source through these endpoints.

## Runtime-only persistence

`db-sync` continues to reconcile only Git-tracked shared tables. Submission/release tables intentionally have no foreign key to the derived `projects` table so a sync delete/reinsert cannot erase immutable delivery history.

Runtime tables:

```text
submission_settings
project_submissions
submission_releases
```

`docker compose down` preserves the named runtime volume. `docker compose down -v` intentionally removes runtime authentication, review, run-history, submission, and release state.
