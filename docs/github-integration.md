# GitHub integration

The platform uses GitHub in two separate ways. Keeping them distinct is important for both security and architecture.

## 1. Read-only contribution integration

The professor dashboard and AI project snapshots can consume repository signals such as:

- repository/default-branch status,
- recent commits,
- pull requests and merged/open PR counts,
- contribution timeline,
- explicit member GitHub identity mappings.

This path uses `GITHUB_*` configuration and is a read model. GitHub failures must not block the core local application.

### Identity mapping

A member is linked only through the optional tracked field:

```json
{
  "id": "hossein",
  "display_name": "Hossein",
  "role": "Developer",
  "github_username": "HoosseinRahimi"
}
```

Never guess another member's GitHub account from a name or email.

### Read configuration

```text
GITHUB_INTEGRATION_ENABLED=true
GITHUB_REPOSITORY=HoosseinRahimi/ForgeFlow-AI-Core
GITHUB_CACHE_TTL_SECONDS=60
GITHUB_API_TIMEOUT_SECONDS=5
```

`GITHUB_TOKEN` is optional for public repositories and should be a runtime-only read token when needed for private access or higher rate limits.

Professor endpoint:

```text
GET /api/professor/github
```

The endpoint does not accept an arbitrary repository or GitHub identity from request parameters.

## 2. Governed AI GitHub writes

The AI autonomy layer may create a branch, issue, or pull request, but only through the authenticated action engine:

```text
propose -> approve -> execute
```

These write operations use separate server-only configuration:

```text
AI_GITHUB_REPOSITORY=HoosseinRahimi/ForgeFlow-AI-Core
AI_GITHUB_TIMEOUT_SECONDS=15
AI_GITHUB_TOKEN=<server-only token>
```

Supported write action kinds currently include:

- `github-branch`
- `github-issue`
- `github-pull-request`

No write occurs merely because a model suggests it. The action must exist as a pending record, be explicitly approved by the owning authenticated student, and then be executed through an allowlisted handler.

The browser never supplies the write token and the model cannot choose a credential. GitHub execution results/failures are persisted in the AI action audit record.

## Evidence links and progress

Activities can be linked to GitHub evidence of type branch, commit, pull request, or issue. Progress synchronization can then infer:

- branch/commit/open-PR evidence -> `in-progress`
- verifiably merged linked PR -> `completed`

`apply=false` previews inferred changes. `apply=true` routes updates through the authoritative activity write service so Git-tracked JSON remains the shared source of truth.

## Security summary

- read and write credentials are separate,
- repository selection comes from trusted runtime configuration,
- write side effects require explicit approval,
- network calls use timeouts,
- tokens are server-only and never returned to the frontend,
- GitHub signals are useful evidence, not a productivity score or the authoritative task database.

See `docs/ai-autonomy-platform.md` and `SECURITY.md`.
