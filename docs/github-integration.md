# GitHub integration

Phase 4 adds a **read-only GitHub contribution view** to the professor dashboard.
It is intentionally separated from the core activity dashboard so temporary
GitHub failures never block local project data.

## What the professor sees

For the configured repository the dashboard shows:

- repository name, default branch, last push, and open PR count
- per-member recent default-branch commit count
- per-member pull request, merged PR, and open PR counts
- latest linked contribution timestamp
- a combined recent commit / pull-request timeline

These numbers are repository signals, **not a productivity score**. Commit counts
cover the recent commits returned for the repository default branch. Work that is
only on an unmerged branch may not appear in the commit count, while its pull
request can still appear in PR metrics.

## Identity mapping

A member is linked only through the optional tracked field:

```json
{
  "id": "hossein",
  "display_name": "Hossein",
  "role": "Developer",
  "github_username": "HoosseinRahimi"
}
```

Add the real GitHub username to `data/users/<id>.json`, then run:

```bash
make db-sync
```

Never guess another member's GitHub account from a name or email. Unlinked
members remain visible as `not linked`.

## Configuration

Defaults are listed in `.env.example`:

```text
GITHUB_INTEGRATION_ENABLED=true
GITHUB_REPOSITORY=HoosseinRahimi/team-project
GITHUB_CACHE_TTL_SECONDS=60
GITHUB_API_TIMEOUT_SECONDS=5
```

Public repositories can be read without authentication, subject to GitHub's
lower unauthenticated API rate limits.

For a private repository or higher API limits, provide a fine-grained token at
runtime only:

```bash
export GITHUB_TOKEN='...'
```

Do not put the token in Git-tracked files. The integration needs read access only.
For the current repository, grant the minimum repository metadata / contents /
pull-request read permissions required by GitHub for the API calls.

Docker Compose forwards the same variables into the backend container.

## API

Professor-only endpoint:

```text
GET /api/professor/github
```

The endpoint never accepts a repository or username from request parameters.
Repository configuration comes from the trusted runtime environment and user
mapping comes from validated tracked user data.

The response has two states:

- `ok`: repository/member/timeline data is present
- `unavailable`: the integration is disabled, misconfigured, timed out, rate
  limited, or temporarily unavailable

An unavailable GitHub response does not affect `/api/professor/dashboard`.

## Request behavior

A refresh performs at most three GitHub API calls:

1. repository metadata
2. up to 100 recent commits from the default branch
3. up to 100 recent pull requests

The assembled response is cached in-process for 60 seconds by default. This
keeps the professor page responsive and reduces rate-limit pressure.

## CI behavior

Browser E2E explicitly sets:

```text
GITHUB_INTEGRATION_ENABLED=false
```

so CI does not depend on external GitHub availability. The GitHub aggregation
logic is tested with deterministic fixtures/mocks instead.

## Security properties

- professor authorization is enforced by FastAPI, not the frontend
- integration is read-only
- GitHub API host is fixed to `api.github.com`
- repository is validated as `owner/repository`
- user mapping is explicit and validated
- `GITHUB_TOKEN` is never returned to the frontend or logged by this service
- network errors return a generic offline-safe response
