# Final Release Checklist

Use this checklist only after the team has completed the real runtime delivery flow. A green pull-request CI run is necessary but is not a substitute for Phase 11 runtime readiness.

## 1. Repository state

- [ ] `git switch main`
- [ ] `git pull --ff-only`
- [ ] `git status --short` is empty
- [ ] `make release-verify` passes
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

## 4. Package verification

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

## 5. Tagging

Run:

```bash
make release-tag
```

The command creates an annotated local tag only after re-running the strict delivery preflight and checksum validation.

Before publishing:

- [ ] inspect `git show v<VERSION>`
- [ ] confirm tag points to the expected `main` commit
- [ ] confirm release notes and artifact checksum one final time

Then publish deliberately:

```bash
git push origin v<VERSION>
```

## 6. University handoff

Provide the professor with:

- repository URL
- release tag
- release notes
- source archive and SHA-256 checksum when requested
- `docs/professor-handoff.md`
- any runtime credentials through a private channel only, never through Git

Do not ship the local runtime SQLite database unless the university explicitly requires it and its sensitive contents have been reviewed separately.
