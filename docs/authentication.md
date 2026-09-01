# Authentication and authorization

The application uses local accounts stored only in the runtime SQLite database. Credentials are deliberately separated from Git-tracked identity data under `data/users/`.

## Roles

- `student`: linked to exactly one tracked `user_id`; can read that user's profile, activities, and projects and can create/update/delete only that user's activities.
- `professor`: not linked to a tracked student; can read all users, activities, projects, and the professor dashboard. Professor access is intentionally read-only.

Authorization is enforced by the FastAPI backend. Frontend routing is convenience only and must never be treated as a security boundary.

## Passwords

Passwords are hashed with Argon2 through `pwdlib`. Plaintext passwords and password hashes must never be committed to Git, placed in `data/`, or added to `.env.example`.

Create or rotate an account interactively after `make setup`:

```bash
make auth-bootstrap
```

Non-interactive provisioning for local automation can use a temporary shell environment variable:

```bash
AUTH_BOOTSTRAP_PASSWORD='replace-me' \
  .venv/bin/python -m backend.auth.bootstrap \
  --username hossein --role student --user-id hossein

AUTH_BOOTSTRAP_PASSWORD='replace-me-too' \
  .venv/bin/python -m backend.auth.bootstrap \
  --username professor --role professor
```

Do not save those commands with real passwords in shell scripts or repository files.

For Docker:

```bash
docker compose up -d --build
docker compose exec backend python -m backend.auth.bootstrap
```

The Docker runtime database is stored in the `team-runtime` volume so local account/session state survives container recreation.

## Sessions

Successful login creates a random session token. Only a SHA-256 digest of that token is stored in SQLite. The browser receives the raw token in an HttpOnly cookie.

Defaults:

- cookie: `team_session`
- `HttpOnly`: enabled
- `SameSite=Lax`
- `Secure`: controlled by `AUTH_COOKIE_SECURE` and should be `true` behind HTTPS
- lifetime: 8 hours, configurable with `AUTH_SESSION_HOURS`

Password rotation deletes existing sessions for that account.

## CSRF

Every session also owns an independent CSRF token. `POST`, `PUT`, and `DELETE` operations require the token through the `X-CSRF-Token` header. The frontend receives the token from `/api/auth/login` or `/api/auth/me` and keeps it in memory.

## Endpoints

```text
POST /api/auth/login
GET  /api/auth/me
POST /api/auth/logout
GET  /api/professor/dashboard
```

All `/api/users`, `/api/activities`, and `/api/projects` endpoints except health now require authentication and apply role/ownership filtering.

## Operational rules

1. Do not add public registration without a separate security review.
2. Do not place authentication secrets in Git-tracked JSON.
3. Never trust a user id supplied by the frontend for authorization; compare it to the authenticated session on the backend.
4. Professor writes require an explicit future product decision and new tests.
5. Authentication/database/schema/CI changes require Tech Lead review via CODEOWNERS.
