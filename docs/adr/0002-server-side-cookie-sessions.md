# ADR 0002: Server-side cookie sessions for local authentication

- Status: Accepted
- Date: 2026-09-01

## Context

Phase 3 requires student/professor authentication and authorization. The application is a local modular monolith with a React frontend, FastAPI backend, and SQLite runtime state. Authentication credentials must not become part of Git-tracked source data.

## Decision

Use local authentication accounts and revocable server-side sessions stored in SQLite.

- Passwords use Argon2 hashes through `pwdlib`.
- A student account links to one tracked user id.
- A professor account has no student user id and is read-only.
- Session tokens are random; only their SHA-256 digests are persisted.
- The browser receives the session token as an HttpOnly, SameSite=Lax cookie.
- Unsafe requests require a separate CSRF token in `X-CSRF-Token`.
- Authentication and authorization are enforced in FastAPI dependencies/routes, not by React routing.

## Why not JWT

JWTs add token-signing, expiry, revocation, refresh-token, and client-storage decisions that are unnecessary for this same-origin/local application. Server-side sessions make logout, password rotation, and revocation straightforward and keep the authority in the existing SQLite runtime.

## Consequences

- Runtime SQLite now contains non-Git authentication state and must persist for Docker users.
- Docker uses a named runtime volume.
- Local account provisioning is an explicit CLI operation.
- CORS must allow credentials only for explicit development origins.
- Future HTTPS deployments must enable `AUTH_COOKIE_SECURE=true`.
- Any future public registration, password reset, or professor write capability requires a new security review/ADR.
