# Public Architecture Overview

The platform is a modular monolith with a React/TypeScript frontend, FastAPI backend, SQLite runtime database, Git-tracked project/activity source data, and optional external AI/GitHub integrations.

## Layers

### Frontend

- React + TypeScript
- role-aware student/professor routes
- project, activity, calendar, timeline, review and AI workspace views
- typed API client contracts

### Backend

- FastAPI application
- explicit schemas and service modules
- session authentication, CSRF checks and ownership authorization
- project integration, review, submission, release-preflight and AI services

### Data

Two categories are intentionally separated:

1. Git-tracked shared source data for collaborative project/activity state
2. Runtime SQLite state for sessions, reviews, submissions, AI threads, memory, actions, health snapshots and notifications

### GitHub boundary

The platform has two distinct GitHub surfaces:

- read-oriented contribution intelligence for commits and pull requests
- governed server-side write actions that require runtime credentials and explicit approval

Public code and documentation must never contain real tokens.

### AI boundary

AI features support provider-backed execution when configured and deterministic fallback where appropriate. Repository retrieval uses bounded lexical chunk retrieval in the current release. It should not be described as vector or embedding-based semantic search.

Governed actions use:

`propose -> approve -> execute`

The model is not trusted with unrestricted shell, filesystem, credential or GitHub access.

## Security principles

- secrets stay server-side
- project/user ownership is checked before data access
- CSRF protects authenticated durable writes
- AI requests are bounded and rate-limited
- repository indexing restricts roots, suffixes and file sizes
- external requests use timeouts
- automatic evidence-backed progress mutation is opt-in
- CI includes lint, tests, E2E, dependency audits and CodeQL

## Public showcase boundary

The Community Showcase documents the architecture and selected reusable concepts, but excludes private team data, deployment state, credential-bearing configuration, private submissions and runtime databases.
