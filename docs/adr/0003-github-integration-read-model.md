# ADR 0003: GitHub contribution data is a read-only external read model

- Status: Accepted
- Date: 2026-09-02

## Context

The professor needs to compare declared project activity with real repository
work such as commits and pull requests. GitHub is external, rate limited, and can
be temporarily unavailable. It also has a different identity model from the
project's tracked users.

Making GitHub authoritative would couple the local academic application to an
external service and would weaken the reproducible `git pull -> run locally`
workflow.

## Decision

GitHub contribution data is treated as a **read-only external read model**.

- Shared users/activities/projects remain authoritative in Git-tracked JSON.
- Each tracked user may explicitly declare `github_username`.
- The backend reads a configured repository from GitHub's API.
- Only professor routes expose aggregated GitHub contribution data.
- The external read is isolated behind `/api/professor/github`.
- Failures return an unavailable state and never break the core professor
  dashboard.
- Results are cached briefly in process to reduce latency/rate-limit pressure.
- CI uses deterministic mocked fixtures rather than requiring GitHub network
  availability.

## Consequences

### Positive

- the application remains locally reproducible and offline-tolerant
- no GitHub token or volatile contribution data is committed
- identity attribution is explicit instead of guessed
- professor analytics can evolve without changing core activity authority
- API rate-limit exposure stays small

### Trade-offs

- recent commit counts only represent the returned default-branch window
- unmerged branch commits may not appear until merged
- in-process cache is per backend process, which is acceptable for this local
  modular monolith but would need replacement for multi-instance deployment
- private repositories require a runtime token

## Rejected alternatives

### Store GitHub metrics in SQLite as authoritative data

Rejected because metrics become stale, require a synchronization lifecycle, and
are reproducible from GitHub when needed.

### Let the frontend call GitHub directly

Rejected because it would expose tokens/configuration to the browser, duplicate
mapping logic, and bypass professor authorization at the backend boundary.

### Infer GitHub usernames from display names or commit emails

Rejected because attribution could be wrong and would create a privacy and data
quality problem. Only explicit `github_username` mappings are accepted.
