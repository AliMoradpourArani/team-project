---
name: forgeflow-tests
description: Run and extend ForgeFlow backend (pytest) and frontend (vitest) tests following repository conventions, including the fake SSE streaming-provider pattern.
---

# ForgeFlow testing

Use this skill when adding or updating tests in this repository.

## Commands

- Backend tests: `.venv/bin/python -m pytest tests -q` (run from the repo root).
- Backend lint: `.venv/bin/python -m ruff check backend tests`.
- Frontend tests: `npm test --prefix frontend` or `npx vitest run <file>` inside `frontend/`.
- Frontend checks: `npx tsc --noEmit` and `npm run lint` inside `frontend/`.
- Full delivery gate: `./scripts/test.sh`.

## Backend conventions

- Each API area has a `tests/test_<area>.py` module with a `client` fixture that copies
  `data/` into `tmp_path`, points `DATABASE_PATH` at a fresh SQLite file via
  `monkeypatch.setenv`, and calls `initialize_database(path, seed=True)`.
- Authentication: `login(client, username, password)` returns the CSRF token; every
  mutating request must send `X-CSRF-Token`.
- Isolation: reset module-level caches with `monkeypatch.setattr` (for example the
  `_RATE_BUCKETS` defaultdict in `backend/services/ai_autonomy.py`) so tests never
  depend on execution order.
- Streaming provider tests fake `urllib.request.urlopen` via
  `monkeypatch.setattr("backend.services.ai_agent.request.urlopen", fake)` and return a
  `_FakeStreamResponse` that yields encoded `data: ...` lines, supports the context
  manager protocol, and exposes a `status` attribute. Raise inside `__iter__` to
  simulate a mid-stream failure.
- Assert on the parsed SSE event sequence (`start` → `delta`* → `done`), the persisted
  thread messages, and `provider`/`providerMessage` fields.

## Frontend conventions

- API functions are mocked with `vi.mock("../api", () => ({ ... }))` and driven with
  `vi.mocked(...)`; never hit the network.
- Render with Testing Library, query by role/text/placeholder from the English
  translations (components fall back to the default i18n context outside the provider).
- Flush async state updates inside `await act(async () => { ... })` and assert final
  UI state; avoid asserting transient intermediate renders.
- For streaming UI tests, mock the streaming API function to call the `onDelta`
  callback and resolve with the full `AIAgentReply`.

## Expectations

- New backend behavior needs a test that fails without the behavior.
- Keep the full `pytest` suite green (single-digit seconds); frontend `tsc` and
  `eslint` must stay clean.
- Cover the failure paths, not only the happy path: auth/CSRF rejection, ownership
  isolation, provider outages and malformed payloads, and rate limiting.
