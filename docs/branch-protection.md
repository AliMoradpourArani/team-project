# Recommended branch protection for `main`

Configure in GitHub: **Settings → Branches → branch protection for `main`**.
The goal is simple: every change, including changes from repository admins,
should travel through a reviewed pull request and pass automated checks.

| Setting | Value |
| --- | --- |
| Require a pull request before merging | ✅ enabled |
| Required approvals | 1 |
| Dismiss stale approvals on new commits | ✅ enabled |
| Require review from Code Owners | ✅ enabled |
| Require conversation resolution | ✅ enabled |
| Require status checks to pass | ✅ enabled |
| Require branches to be up to date | ✅ enabled |
| Do not allow bypassing the above settings | ✅ enabled |
| Allow force pushes | ❌ disabled |
| Allow deletions | ❌ disabled |
| Require linear history | ✅ enabled |
| Squash merge | ✅ enabled |

## Required checks

Keep the existing stable checks required:

- `conflict-marker-check`
- `backend`
- `frontend`

After the Phase 2.5 workflows have run successfully at least once, also require:

- `e2e`
- `dependency-review`
- `python-audit`
- `frontend-audit`
- `codeql (python)`
- `codeql (javascript-typescript)`

The `AI Review / ai-review` check should only become required after the
`OPENAI_API_KEY` repository secret has been configured and a test pull request
has confirmed the reviewer works. Until that secret exists, the workflow exits
successfully with AI review disabled so normal development is not blocked.

## CODEOWNERS

`.github/CODEOWNERS` assigns high-risk platform areas to the Tech Lead. With
**Require review from Code Owners** enabled, changes to CI, database internals,
schemas, dependency manifests, Docker integration, and architecture contracts
cannot merge without that review.

## Why admin bypass is disabled

GitHub branch protection normally allows administrators to bypass protections.
Enable **Do not allow bypassing the above settings** so the project lead follows
the same PR process as the rest of the team. This protects `main` from accidental
direct commits and keeps the repository workflow demonstrable to the team.
