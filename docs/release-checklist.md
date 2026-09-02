# Final Release Checklist

Use this checklist only after the team has completed the real runtime delivery flow. A green pull-request CI run is necessary but is not a substitute for Phase 11 runtime readiness.

## 1. Repository state

- [ ] `git switch main`
- [ ] `git pull --ff-only`
- [ ] `git status --short` is empty
- [ ] `make release-verify` passes
- [ ] `make academic-submission-verify` passes
- [ ] `VERSION` matches the intended stable tag
- [ ] release notes exist at `docs/releases/v<VERSION>.md`

## 2. Team delivery state

- [ ] every tracked project is Phase 10 `READY`
- [ ] every project has its intended final frozen submission
- [ ] professor reviews are `approved`
- [ ] every approval is recorded after the latest frozen submission
- [ ] `make delivery-preflight` exits successfully
- [ ] the professor Final Delivery Control shows release-candidate ready

## 3. Demo verification

- [ ] `make demo-handoff` completes on a clean local checkout
- [ ] professor login works
- [ ] team dashboard loads
- [ ] every member project detail page loads
- [ ] preview-only demos render correctly
- [ ] reviewed executable demos work when explicitly enabled
- [ ] frozen submissions and review results are visible as expected

## 4. Release package verification

Run:

```bash
make release-package
```

Then verify:

- [ ] archive exists under `dist/release-v<VERSION>/`
- [ ] `.sha256` file exists
- [ ] `release-manifest.json` points to the current `main` commit
- [ ] `sha256sum -c <archive>.sha256` passes from inside the artifact directory
- [ ] archive does not contain `.env`, runtime databases, sessions, tokens, virtual environments, dependency directories, or local build output

## 5. Academic submission bundle and freeze

Run:

```bash
make academic-submission
make academic-freeze-verify
```

Then verify:

- [ ] outer academic bundle and `.sha256` exist under `dist/`
- [ ] inner `SHA256SUMS` passes
- [ ] `academic-submission-manifest.json` points to the current `main` commit
- [ ] academic manifest records `preflightReady: true`
- [ ] runtime state and credentials are explicitly excluded
- [ ] release package, academic bundle, and intended tag all point to the same commit
- [ ] repository freeze policy in `docs/repository-freeze.md` is in effect

If any release-blocking code or documentation change is merged after this point, rebuild and re-verify the bundle from the new `main` commit.

## 6. Tagging

Run:

```bash
make release-tag
```

The command creates an annotated local tag only after re-running the strict delivery preflight, release checksum validation, and Phase 14 academic-freeze verification.

Before publishing:

- [ ] inspect `git show v<VERSION>`
- [ ] confirm tag points to the expected `main` commit
- [ ] confirm release notes and both release/academic artifact checksums one final time

Then publish deliberately:

```bash
git push origin v<VERSION>
```

## 7. University handoff

Provide the professor with:

- repository URL
- release tag
- `team-project-academic-submission-v<VERSION>.tar.gz`
- outer SHA-256 checksum
- release notes
- professor handoff guide included in the academic bundle
- any runtime credentials through a private channel only, never through Git

Do not ship the local runtime SQLite database unless the university explicitly requires it and its sensitive contents have been reviewed separately.
