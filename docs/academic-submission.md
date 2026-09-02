# Academic Submission Bundle

Phase 14 turns the stable release target into one university handoff bundle without weakening the private/runtime boundaries used by authentication, review, and submission state.

## Build command

Run only after the real team runtime passes the strict Phase 11 preflight:

```bash
make academic-submission
```

The command is intentionally strict. It requires:

- current branch is `main`,
- working tree is clean,
- local `main` exactly matches `origin/main`,
- Phase 13 release contract validates,
- Phase 11 final-delivery preflight is READY,
- the Phase 13 release package is bound to the same commit/version/tag target.

## Output

For `VERSION=1.0.0`:

```text
dist/academic-submission-v1.0.0/
├── team-project-v1.0.0.tar.gz
├── team-project-v1.0.0.tar.gz.sha256
├── release-manifest.json
├── preflight.json
├── PROFESSOR_HANDOFF.md
├── ACADEMIC_SUBMISSION.md
├── REPOSITORY_FREEZE.md
├── RELEASE_NOTES.md
├── academic-submission-manifest.json
└── SHA256SUMS

dist/team-project-academic-submission-v1.0.0.tar.gz
dist/team-project-academic-submission-v1.0.0.tar.gz.sha256
```

## Integrity model

The academic manifest pins:

- semantic version,
- intended Git tag,
- exact Git commit,
- commit timestamp,
- bundle generation timestamp,
- source release archive name and SHA-256,
- successful final-preflight state,
- explicit absence of runtime state and credentials.

`SHA256SUMS` covers every file inside the handoff directory. The outer academic tarball gets its own SHA-256 file.

## Security boundary

The source archive is inherited from the Phase 13 `git archive` package. Therefore ignored or untracked local material is not part of the source payload.

The academic bundle must never include:

- SQLite runtime databases,
- password hashes or passwords,
- session or CSRF tokens,
- `.env` files,
- GitHub/API tokens,
- local virtual environments,
- `node_modules`, caches, logs, or local build output.

`preflight.json` is a readiness report, not a runtime database export.

## Professor verification

A reviewer can verify the outer bundle first:

```bash
sha256sum -c team-project-academic-submission-v1.0.0.tar.gz.sha256
```

After extraction, verify every included file:

```bash
cd academic-submission-v1.0.0
sha256sum -c SHA256SUMS
```

Then follow `PROFESSOR_HANDOFF.md` to run the application locally.

## Relationship to v1.0.0

Creating this bundle does not publish a Git tag. `v1.0.0` remains a deliberate final action through the guarded Phase 13 release-tag flow after the bundle and freeze checklist are reviewed.
