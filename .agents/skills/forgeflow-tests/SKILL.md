---
name: forgeflow-tests
description: Run and extend ForgeFlow backend (pytest) and frontend (vitest) tests following repository conventions, with uncompromising verification discipline — prove tests fail without the behavior, and never claim green without running the exact commands.
---

# ForgeFlow testing

Use this skill when adding or updating tests in this repository. Rigor is not
optional here: every claim you make about a test must be backed by evidence you
produced in this session, and every assumption must be checked against the
actual code before you rely on it.

## Commands

- Backend tests: `.venv/bin/python -m pytest tests -q` (run from the repo root).
- Backend lint: `.venv/bin/python -m ruff check backend tests`.
- Frontend tests: `npm test --prefix frontend` or `npx vitest run <file>` inside `frontend/`.
- Frontend checks: `npx tsc --noEmit` and `npm run lint` inside `frontend/`.
- Full delivery gate: `./scripts/test.sh` — run it when shared fixtures/conftest
  change or the change spans backend *and* frontend; otherwise targeted suites
  plus the full `pytest -q` run.

## Scope gate — interrogate before you write

Before writing or extending any test, answer each of these from concrete
evidence (a file you read, a symbol you found), not from memory or guesswork:

1. **Behavior:** What exact behavior is under test, in which file and function?
2. **Surface:** Which endpoint/component/test module exercises it, and what do
   that module's existing fixtures and helpers actually look like?
3. **Failure paths:** What are the failure cases (auth/CSRF rejection, ownership
   isolation, provider outage, malformed payload, rate limiting), and which of
   them are in scope for this change?
4. **Red proof:** What specifically makes a test for this behavior fail if the
   behavior is missing or broken?

If any answer is a guess, resolve it from the repository first: read the
module that defines the behavior, fixture, helper, or string before
considering a question to the user — asking what you could have looked up
yourself is an unnecessary interruption. Only if ambiguity genuinely remains
after inspecting the defining code, ask the user one focused round of
clarifying questions, get precise answers, and only then start writing.
Banned: assuming fixture names, endpoint paths, helper signatures, or i18n
strings without reading the module that defines them.

Escalation: for large changes — a new API area or test module, a new component,
or any fixture/conftest, schema, or shared-helper change — run a structured
interview before writing a single test. Invoke the `grilling` skill if it is
available in this environment; if it is not, run the same interview inline:
map the decision tree, ask every currently-answerable question in one numbered
round with recommended answers, wait for responses, and iterate until nothing
is left silently assumed. The escalation must never block on a missing skill —
the interview discipline is the requirement, not the tool. The single focused
round remains the default for small, unambiguous changes.

## Evidence discipline — never claim what you haven't run

- Never report a test as passing unless you executed the exact command in this
  session and read its output.
- Quote the relevant lines of actual output when summarizing results — no
  paraphrasing a pass you did not see.

### Proof of sensitivity (backend and frontend)

- Red/green: every new behavior — backend or frontend — requires running the
  new test against the behavior absent or un-fixed and capturing the failure,
  then running it again with the behavior in place and capturing the pass.
- Mutation check ("kill your own test"): after every new test passes,
  temporarily break the code under test, watch the test fail, revert, watch it
  pass again. This proves the test is sensitive to the behavior and not green
  by accident (for example, a mock swallowing the assertion). Mutations must
  be safe and self-cleaning:
  - Isolated and minimal: one mutation at a time — the smallest single edit
    that disables the behavior under test — and only within the files this
    task is already changing. Never mutate shared fixtures, config, scripts,
    or anything outside the current change's scope.
  - Restored immediately: revert the mutation in the very next step, before
    any other command. Never leave mutated code in place across steps, and
    never commit or push mutated code.
  - No-residue verification: after reverting, run `git diff` and `git status`
    and confirm the working tree is byte-identical to its pre-mutation state
    before continuing. If anything differs, restore it and re-verify. State
    in the report that the residue check was performed and clean.
- Extending an existing test: perform red/green or one mutation check, and
  state which proof you performed.

## Backend conventions (pytest)

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

### Backend precision rules

- Read the target `tests/test_<area>.py` module first and reuse its `client`
  fixture and helpers; never reinvent a fixture that already exists.
- Cover the failure paths, not only the happy path: auth/CSRF rejection,
  ownership isolation, provider outages and malformed payloads, and rate
  limiting. When you skip one, say so and why.
- Keep the full `pytest` suite green and in single-digit seconds. Flag any test
  that sleeps, waits on real I/O, or could flake.

## Frontend conventions (vitest)

- API functions are mocked with `vi.mock("../api", () => ({ ... }))` and driven with
  `vi.mocked(...)`; never hit the network.
- Render with Testing Library, query by role/text/placeholder from the English
  translations (components fall back to the default i18n context outside the provider).
- Flush async state updates inside `await act(async () => { ... })` and assert final
  UI state; avoid asserting transient intermediate renders.
- For streaming UI tests, mock the streaming API function to call the `onDelta`
  callback and resolve with the full `AIAgentReply`.

### Frontend precision rules

- Verify the exact strings you query by role/text/placeholder exist in the
  English translations (`frontend/src/i18n/`) before asserting on them.
- Mock at the API boundary only; a test that performs a real `fetch` is wrong.
- Before claiming done, run all three and require clean output:
  `npx vitest run <file>`, `npx tsc --noEmit`, `npm run lint`.

## Final gate — the definition of done

A testing task is complete only when all of the following are true and you can
cite the command output for each:

- [ ] Full backend suite green: `.venv/bin/python -m pytest tests -q`
- [ ] Backend lint clean: `.venv/bin/python -m ruff check backend tests`
- [ ] Frontend (if touched): targeted vitest file, `tsc --noEmit`, and `eslint` all clean
- [ ] Red/green proof for every new behavior (backend and frontend)
- [ ] Mutation check for every new test; named proof for test extensions;
      clean no-residue verification (`git diff` / `git status`) after each
- [ ] `./scripts/test.sh` passed end to end when fixtures/conftest changed or the
      change spans backend and frontend
- [ ] Report in the exact template below

## Report — mandatory end-of-task format

- **Ran:** every command executed, in order
- **Evidence:** quoted key output lines (pass *and* fail)
- **Proof:** red/green and/or mutation check performed, and where
- **Not tested:** what was skipped, and why
- **Risks:** residual concerns the user should know
