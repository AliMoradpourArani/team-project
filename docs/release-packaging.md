# Release Packaging & Version Tagging

Phase 13 turns the local-first delivery workflow into a guarded stable-release process without pretending that GitHub CI can reproduce the professor's private runtime state.

## Version source

`VERSION` is the single project-release target for packaging and tagging. The current target is `1.0.0`, corresponding to annotated Git tag `v1.0.0`.

The API has its own compatibility version and does not need to equal the project release version.

## Two levels of validation

### CI-safe static validation

```bash
make release-verify
```

This validates:

- stable semantic VERSION format;
- matching versioned release notes;
- final release checklist presence;
- release script presence and Bash syntax.

CI runs this check on every pull request. It does not claim that the final university runtime is ready.

### Runtime release validation

```bash
make delivery-preflight
```

This is the authoritative Phase 11 gate. It depends on real private/runtime state such as student accounts, professor reviews, frozen submissions, and approval ordering.

`make release-package` and `make release-tag` both require this strict gate to pass again locally.

## Building the package

From a clean, up-to-date `main` checkout:

```bash
make release-package
```

The command:

1. verifies the release contract;
2. requires a clean `main` worktree;
3. re-runs strict Phase 11 preflight;
4. archives only Git-tracked source with `git archive`;
5. uses deterministic gzip metadata (`gzip -n`);
6. writes a SHA-256 checksum;
7. writes a small release manifest bound to version, tag, commit, commit date, archive, and checksum.

Output lives under:

```text
dist/release-v1.0.0/
├── team-project-v1.0.0.tar.gz
├── team-project-v1.0.0.tar.gz.sha256
└── release-manifest.json
```

`dist/` is ignored by Git.

## Sensitive state boundary

The source artifact intentionally excludes:

- runtime SQLite databases;
- authentication accounts/password hashes;
- active sessions;
- API tokens;
- `.env` files;
- Python virtual environments;
- `node_modules`;
- local build/cache output.

This follows the existing architecture where Git-tracked source and private runtime state remain separate.

## Tagging

After inspecting the package and completing `docs/release-checklist.md`:

```bash
make release-tag
```

The tag command refuses to continue unless:

- the current branch is `main`;
- the worktree is clean;
- local `main` exactly matches `origin/main`;
- the intended tag does not already exist;
- release static verification passes;
- Phase 11 strict preflight passes;
- the package and checksum exist;
- the package checksum is valid;
- the release manifest version/tag/commit/checksum exactly match current HEAD and artifact.

It then creates an **annotated local tag**. It does not push automatically.

Publish deliberately only after final inspection:

```bash
git push origin v1.0.0
```

## Why GitHub Actions does not create the stable tag

The final-delivery decision includes private local runtime state that is intentionally not committed to Git. A cloud workflow using a synthetic database cannot prove that the real professor reviews, frozen submissions, and account links are ready.

Therefore CI validates the release machinery, while the official package/tag operation remains tied to the strict local preflight.
