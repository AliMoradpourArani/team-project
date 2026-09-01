# Architecture Decision Records (ADRs)

Use an ADR when a decision changes a shared contract, architecture boundary, data
model, security posture, or development workflow. Small implementation details do
not need an ADR.

## Format

Create `NNNN-short-title.md` with:

```md
# ADR NNNN: Title

Status: Proposed | Accepted | Superseded
Date: YYYY-MM-DD

## Context
What problem or constraint caused the decision?

## Decision
What are we choosing?

## Consequences
What becomes easier, harder, required, or intentionally out of scope?
```

Once an ADR is accepted and merged, do not rewrite its history to make a later
decision look original. Add a new ADR and mark the old one superseded.
