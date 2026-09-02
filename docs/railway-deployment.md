# Railway production deployment

The main application is packaged as one production service: React is built during the Docker image build and served by the FastAPI process. This keeps the frontend, backend, authentication cookies, API and AI workspace on one origin.

## Railway service

Connect the private `HoosseinRahimi/ForgeFlow-AI-Core` repository and deploy from the repository root. Railway detects the root `Dockerfile` automatically.

Recommended service settings:

- Healthcheck path: `/health`
- Restart policy: on failure
- Replica count: `1`
- Public networking: enabled

The application listens on Railway's injected `PORT` variable.

## Persistent volume

Attach one Railway Volume to the service and mount it at:

`/app/data`

This is required. The Git-tracked source data is mutable at runtime and the SQLite runtime database lives at `/app/data/.runtime/team-project.db`. The startup script seeds an empty volume from the image once, then preserves later runtime changes across redeployments.

Do not mount a volume over `/app` because it would hide the application image.

## Required production variables

Set these in Railway Variables:

```text
AUTH_COOKIE_SECURE=true
CORS_ORIGINS=
GITHUB_INTEGRATION_ENABLED=true
GITHUB_REPOSITORY=HoosseinRahimi/ForgeFlow-AI-Core
AI_AUTOMATION_ENABLED=true
AI_AUTOMATION_APPLY_PROGRESS=false
PROJECT_RUNNER_ENABLED=false
```

`CORS_ORIGINS` can remain empty for the normal single-origin Railway deployment. Add explicit origins only if a separate frontend is introduced later.

## Optional server-only secrets

Configure these only in Railway's secret/variable store. Never commit their values:

```text
GITHUB_TOKEN=
AI_API_KEY=
AI_GITHUB_TOKEN=
```

For governed GitHub write actions also set:

```text
AI_GITHUB_REPOSITORY=HoosseinRahimi/ForgeFlow-AI-Core
```

## AI provider configuration

Defaults work without a provider key using deterministic fallback behavior. To enable provider-backed AI:

```text
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-5-mini
AI_API_KEY=<server-only secret>
```

## Database and startup

The container startup sequence is intentionally inside the runtime entrypoint because Railway Volumes are mounted only when the service starts:

1. Create the persistent data/database directories.
2. Seed an empty `/app/data` volume from the image exactly once.
3. Run ordered SQLite migrations and seed synchronization.
4. Start one Uvicorn worker behind Railway's proxy.

A single worker is intentional because the current runtime uses SQLite plus an in-process AI maintenance loop.

## Verification

After Railway reports a healthy deployment, verify:

```text
GET /health        -> {"status":"ok"}
GET /api/health    -> {"status":"ok"}
GET /              -> React application
```

Then sign in and verify one authenticated API flow, project loading, and the AI workspace status endpoint.

## Scaling note

Do not increase replicas while SQLite and mutable JSON source data are stored on a single attached volume. Migrate durable state to a network database/object store before horizontal scaling.
