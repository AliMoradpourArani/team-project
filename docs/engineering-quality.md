# Engineering quality gates

Phase 2.5 adds automated quality and security controls around the shared platform.
The intent is to keep `main` runnable after every merge and make review rules
visible to the whole team.

## Pull-request gates

The main CI workflow runs:

1. unresolved merge-conflict marker detection
2. backend Ruff linting
3. AI reviewer script syntax validation
4. backend pytest suite with a 70% coverage floor
5. fresh SQLite initialization and source-data reconciliation
6. frontend ESLint, Prettier, TypeScript, unit tests, and production build
7. Playwright E2E flow in Chromium against a real FastAPI + Vite stack

The browser test creates an activity through the UI, verifies it in the timeline
and calendar, then deletes it. The runner uses an isolated SQLite database and
throwaway Git checkout, so the repository's real tracked data is not changed.

## Security automation

`.github/workflows/security.yml` runs:

- GitHub dependency review on pull requests when Dependency Graph is enabled
- `pip-audit` for Python runtime dependencies
- `npm audit` for frontend dependencies
- CodeQL for Python and JavaScript/TypeScript
- a scheduled weekly re-check even when no PR is open

If GitHub Dependency Graph is disabled, the workflow detects that condition and
skips only the dependency-review action instead of failing the whole security
suite. Enable Dependency Graph under repository security settings before making
`dependency-review` an enforced branch-protection gate.

Dependabot opens weekly update PRs for Python, frontend npm, E2E Playwright, and
GitHub Actions dependencies.

## Runtime resilience and observability

The API adds an `X-Request-ID` response header and emits structured JSON request
logs with method, path, status, duration, and correlation ID. The frontend has an
application-level Error Boundary so an unexpected render failure produces a
recoverable fallback instead of a blank page.

## AI pull-request reviewer

`.github/workflows/ai-review.yml` uses `pull_request_target` deliberately, but it
never executes pull-request code. It checks out the trusted base revision and
fetches only PR metadata and patch text through the GitHub API. The reviewer has
read access to repository contents and permission to write review comments, but
no contents-write or merge permission.

The reviewer checks project-specific invariants such as JSON source authority,
SQLite reproducibility, append-only migrations, API/data-contract compatibility,
security-sensitive changes, and test adequacy.

### Enable it

Create a GitHub Actions repository secret named:

```text
OPENAI_API_KEY
```

Optionally create a repository variable:

```text
OPENAI_REVIEW_MODEL=gpt-5.6-luna
```

If the API key is absent, the AI job exits successfully with review disabled so
normal PRs are not blocked. Only make `AI Review / ai-review` a required status
check after a test PR proves the configured key/model works.

## CODEOWNERS

`.github/CODEOWNERS` assigns sensitive platform areas to `@HoosseinRahimi`.
Enable **Require review from Code Owners** in branch protection for this file to
become an enforced merge gate.

## Architecture decisions

Record durable architecture or workflow decisions under `docs/adr/`. Add a new
ADR instead of silently rewriting the rationale behind an accepted decision.

## Local equivalents

Most checks can be run locally with:

```bash
make test
python -m pytest --cov=backend --cov-report=term-missing
npm audit --prefix frontend --audit-level=high
```

For E2E testing, install the application dependencies plus `e2e/` dependencies,
install Chromium with Playwright, initialize a throwaway database, and run:

```bash
npm install --prefix e2e
cd e2e
npx playwright install chromium
DATABASE_PATH=/tmp/team-project-e2e.db npm test
```
