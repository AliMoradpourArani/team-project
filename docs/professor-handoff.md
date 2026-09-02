# Professor Handoff Guide

This repository is designed to be cloned and reviewed locally. No public deployment is required.

## 1. Clone and prepare

```bash
git clone https://github.com/HoosseinRahimi/team-project.git
cd team-project
make demo-handoff
```

`make demo-handoff` checks local prerequisites, prepares the Python environment when needed, initializes/synchronizes the local SQLite database, prints the current final-delivery preflight report, and shows the exact commands used to start the application.

## 2. Create local accounts when needed

Authentication state is intentionally not stored in Git. If the local runtime has no professor account yet, run:

```bash
make auth-bootstrap
```

Choose role `professor` for the professor login. Student accounts should link to an existing tracked `user_id`.

Do not commit passwords, password hashes, sessions, or generated runtime database files.

## 3. Start the application

Terminal 1:

```bash
.venv/bin/python -m uvicorn backend.app.main:app --reload
```

Terminal 2:

```bash
npm run dev --prefix frontend
```

Open:

- application: http://localhost:5173
- API: http://localhost:8000
- API documentation: http://localhost:8000/docs

## 4. Recommended review path

1. Sign in as professor.
2. Open the team dashboard and inspect member progress.
3. Open each member project through the generic project detail route.
4. Inspect integration/onboarding gates, README, demo contract, and professor review state.
5. Preview static/OpenAPI projects or run reviewed CLI demos only when the local runner is explicitly enabled.
6. Open Final Delivery Control and inspect any remaining blockers.
7. Review frozen submissions and the release candidate when final-delivery preflight is green.

## 5. Final-delivery commands

Diagnostic report that does not fail:

```bash
make delivery-preflight-report
```

Strict final gate:

```bash
make delivery-preflight
```

The strict command exits nonzero until every tracked project satisfies the Phase 11 release-candidate invariants.

## 6. Safety boundary

The project runner is for reviewed repository code only. It is not a sandbox for untrusted code. Static and OpenAPI previews do not start arbitrary project processes. Runtime authentication, reviews, submissions, releases, and demo history remain local SQLite state and are not written into tracked student source data.
