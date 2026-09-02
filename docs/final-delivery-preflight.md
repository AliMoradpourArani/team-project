# Final Delivery Preflight and Release Candidate

Phase 11 adds one shared final-delivery decision model before the professor freezes a team release candidate.

The goal is not to create another source of truth. The preflight composes the existing tracked project metadata, Phase 10 onboarding model, runtime authentication state, immutable Phase 9 submissions, and professor reviews into one read-only readiness report.

## Final delivery order

The safe order is intentionally strict:

1. integrate the member project until Phase 10 reports `ready`
2. freeze the final project source as an immutable submission
3. review that frozen version and set the professor review to `approved`
4. run the Phase 11 final-delivery preflight
5. freeze the team release candidate only when every blocking gate passes

A professor approval that predates the latest frozen submission does **not** cover that submission. If a student freezes a newer version, the professor must review again after that freeze.

## Global gates

The preflight checks:

- at least one tracked project exists
- a professor account exists in the runtime database
- every tracked project owner has a linked student account
- every tracked project passes the Phase 10 integration/onboarding contract
- every tracked project has an immutable frozen submission
- every latest frozen submission is followed by an approved professor review

## Per-project gates

Each tracked project reports:

- Integration readiness
- Frozen submission
- Professor approval
- Approval covers frozen version

Every failed gate includes a concrete remediation string. The professor UI shows the same model returned by the API and used by the local CLI.

## API

Professor-only read endpoint:

```text
GET /api/professor/preflight
```

The response includes:

- `status`: `ready` or `blocked`
- `releaseCandidateReady`
- project/readiness counts
- total blocker count
- global gates
- per-project gates
- the local validation command

Students cannot access this endpoint.

## Local CLI

Strict final check:

```bash
make delivery-preflight
```

This exits non-zero until the release candidate is ready.

Diagnostic-only report:

```bash
make delivery-preflight-report
```

Equivalent commands:

```bash
.venv/bin/python -m backend.delivery_preflight
.venv/bin/python -m backend.delivery_preflight --report-only
.venv/bin/python -m backend.delivery_preflight --json
```

The CLI uses the current runtime SQLite state. Run database setup/sync and bootstrap the local accounts before expecting the account gate to pass.

## Release guard

`POST /api/professor/releases` re-runs the final-delivery preflight server-side before creating a release.

This means disabling the button in the browser is only a usability feature. The backend remains the security and integrity boundary. A direct HTTP request cannot bypass a blocked preflight.

## CI behavior

Normal CI runs:

```bash
python -m backend.delivery_preflight --report-only
```

against a fresh database as a smoke test. This verifies that the preflight code and schema work without forcing unfinished teammate placeholders to make every development PR fail.

The strict command is deliberately reserved for the actual final-delivery checkpoint.

## Current expected team state

Until Ali and Reza integrate their real member projects and freeze them, the final preflight is expected to report `blocked`.

That is a healthy state, not a CI failure. Phase 10 allows incomplete placeholders during development; Phase 11 is the final gate that refuses to call the team release-ready until every real deliverable is present.

## Trust and storage boundaries

Phase 11 adds no database migration and no new Git-tracked runtime state.

- project metadata/manifests/source remain Git-tracked
- submissions/reviews/accounts/releases remain runtime SQLite state
- preflight is computed on demand and is not persisted
- release candidates remain immutable Phase 9 release manifests

The preflight does not execute arbitrary commands and does not weaken the existing runner, snapshot, CSRF, authorization, or secret-file protections.
