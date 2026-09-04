---
name: forgeflow-feature
description: Mandatory tests-first workflow for every ForgeFlow behavior change — classify the change, prove a green baseline, plan slices, write tests before any implementation, prove red for the right reason, implement to green, and pass the same final gate as forgeflow-tests.
---

# ForgeFlow feature workflow (tests first)

Use this skill **before** implementing any behavior change in this repository:
a new feature, a bug fix, or a refactor that changes observable behavior. Its
one rule: no implementation code exists before its tests exist and have been
seen to fail — for the right reason — in this session.

This skill governs the *ordering and proof* of feature work. It does not
restate test conventions: for commands, fixtures, mocking rules, evidence
discipline, and the report format, read and follow the `forgeflow-tests`
skill (`.agents/skills/forgeflow-tests/SKILL.md`). Where this skill is silent,
that one is authoritative.

## Step 1 — Classify the change

Before anything else, state in writing which category this change is:

- **Behavior change** (feature, fix, behavior-changing refactor): this skill's
  full workflow applies.
- **Docs/comments/types-only** (no observable behavior change): say so
  explicitly and why; skip the cycles, but the final gate still applies to
  whatever the change touches.

If you cannot state the category from concrete evidence, that is the first
thing to resolve — not an assumption to proceed on.

Escalation: for large or ambiguous features — a new API area, a new
component, a schema/migration, or any shared fixture/conftest/helper change —
run a structured interview before Step 2. Invoke the `grilling` skill if it
is available in this environment; if it is not, run the same interview
inline: map the decision tree, ask every currently-answerable question in one
numbered round with recommended answers, and iterate until nothing is left
silently assumed. The escalation must never block on a missing skill.

## Step 2 — Green baseline

Run the existing suite before writing any new test:

- Backend: `.venv/bin/python -m pytest tests -q` (repo root).
- Frontend (if this change will touch it): targeted vitest for the files
  you expect to affect, e.g. `npx vitest run <file>` inside `frontend/`.

The baseline must be green. If it is not, stop: every later "red" is
meaningless until pre-existing failures are fixed or explicitly ruled out.
Quote the baseline output in your final report.

## Step 3 — Slice plan (before any code)

Write a numbered, ordered list of slices before writing any test or
implementation code. Each slice is **one observable behavior** plus the tests
that pin it — an endpoint returning a new shape, a validation rejecting a
payload, a component rendering a new state. Confirm the plan (and its scope:
which failure paths are in and out) with the user before Step 4.

Order slices backend-first, then frontend: the frontend mocks the API
boundary (`vi.mock("../api")`), so the backend contract must exist before
component tests are written against it.

## Step 4 — Per-slice red/green cycle

Work strictly in slice order. For each slice:

1. **Tests first.** Write the slice's tests only, following `forgeflow-tests`
   conventions (reuse existing fixtures; CSRF on mutating requests; mock at
   the API boundary; verify i18n strings before asserting on them). Do not
   write implementation code in this step — not even a "quick scaffold".
2. **Prove red, for the right reason.** Run targeted only:
   `pytest tests/test_<area>.py -q` or `npx vitest run <file>`. Every test
   must fail *because the behavior does not exist yet* — a 404 for the new
   endpoint, an ImportError for the new module, an assertion failure on the
   missing value. Record why each test is red. A red caused by a typo, a
   wrong fixture, or an unrelated failure is not proof; fix the test and
   re-prove.
3. **Implement to green.** Write the minimum implementation that satisfies
   the slice's tests. Re-run the same targeted command and capture the pass.
4. **Mutation check.** Once per slice — on the most load-bearing assertion —
   temporarily break the implementation, watch the slice's tests fail, revert,
   watch them pass. (Tests added outside this flow still follow
   `forgeflow-tests`' stricter per-test rule.)

## Step 5 — Final gate

Identical to `forgeflow-tests` — complete only when you can cite the command
output for each, in this session:

- [ ] Full backend suite green: `.venv/bin/python -m pytest tests -q`
- [ ] Backend lint clean: `.venv/bin/python -m ruff check backend tests`
- [ ] Frontend (if touched): targeted vitest, `npx tsc --noEmit`, and
      `npm run lint` inside `frontend/` all clean
- [ ] `./scripts/test.sh` passed end to end when the change spans backend and
      frontend or touches shared fixtures/conftest
- [ ] Green baseline output quoted (Step 2)
- [ ] Red-for-the-right-reason proof recorded for every slice (Step 4.2)
- [ ] One mutation check per slice performed and named (Step 4.4)
- [ ] Report in `forgeflow-tests`' mandatory format: **Ran** / **Evidence** /
      **Proof** / **Not tested** / **Risks**

This skill stays deliberately silent on git/commit discipline; that is the
user's workflow, not the skill's.
