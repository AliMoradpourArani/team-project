# Repository Freeze Policy

Phase 14 defines the final academic freeze boundary. The repository is not permanently read-only, but the commit selected for academic submission must stop moving while the final bundle, tag, and university handoff are produced.

## Freeze point

Freeze begins only when all of the following are true:

1. every member project is Phase 10 READY,
2. every final source version is frozen,
3. the professor has approved after the latest freeze,
4. `make delivery-preflight` passes,
5. CI and Security are green on the intended `main` commit,
6. `make academic-submission` succeeds for that same commit.

## During freeze

Do not merge ordinary feature work into the frozen commit line.

Allowed changes before publication are limited to release-blocking fixes such as:

- broken setup or professor handoff,
- incorrect checksum/manifest generation,
- security defects,
- data-loss or authorization defects,
- a university-required correction.

Any allowed fix invalidates the previous bundle. After the fix:

```text
CI/Security → final member freeze/review if affected → delivery-preflight → academic-submission
```

must be repeated from the new `main` commit.

## Binding rule

The final academic bundle, Phase 13 release package, and eventual `v1.0.0` tag must all identify the exact same Git commit.

Do not reuse a package or checksum generated from an older commit.

## Final publication sequence

```text
main clean and synced
       ↓
make delivery-preflight
       ↓
make academic-submission
       ↓
verify outer + inner SHA-256
       ↓
review docs/release-checklist.md
       ↓
make release-tag
       ↓
verify tag points to bundle commit
       ↓
git push origin v1.0.0
       ↓
submit academic bundle
```

Tag publication remains deliberate. No script in the repository automatically pushes the stable tag.

## After submission

If development continues after university submission, create new work on normal feature/fix branches and move to a later semantic version. Never silently replace the submitted `v1.0.0` artifact or move an existing stable tag.
