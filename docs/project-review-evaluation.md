# Project Review & Evaluation

Phase 8 adds a professor-owned evaluation workflow on top of the existing project integration and demo system.

## Design goals

- keep authoritative student data and project source unchanged,
- let the professor review every visible project from the shared platform,
- let students read feedback for their own projects,
- keep evaluation state private to the local runtime database,
- require authenticated professor access plus CSRF for all review writes,
- use a fixed typed rubric rather than arbitrary score fields.

## Runtime-only boundary

Project reviews live in SQLite table `project_reviews` created by migration `008_create_project_reviews.sql`.

They are **not** written to:

- `data/projects/*.json`,
- `data/users/*.json`,
- `data/activities/**`,
- `projects/<owner>/<project>/`,
- Git commit history.

This means professor evaluation does not mutate student-owned shared source data.

## Rubric

The rubric totals 100 points:

| Criterion | Maximum |
| --- | ---: |
| Functionality | 30 |
| Code quality | 20 |
| Documentation | 15 |
| Integration | 20 |
| Contribution | 15 |
| **Total** | **100** |

Every score is validated on both the API contract and the SQLite schema boundary.

## Review states

A project with no row in `project_reviews` is considered `pending`.

Persisted states are:

- `in-review`
- `changes-requested`
- `approved`

Deleting a review resets the project to `pending`.

## Authorization

### Student

A student can:

- read the professor review for their own visible project,
- see rubric scores, total score, status, written feedback, and update time.

A student cannot:

- create a review,
- update a review,
- delete a review,
- open the professor review queue,
- read another student's project review.

### Professor

A professor can:

- open the team review queue,
- read every project review,
- create or update a rubric review,
- reset a review back to pending.

Review mutations require a valid authenticated professor session and `X-CSRF-Token`.

## API

```text
GET    /api/professor/reviews
GET    /api/projects/{project_id}/review
PUT    /api/projects/{project_id}/review
DELETE /api/projects/{project_id}/review
```

`PUT` accepts the fixed rubric fields and returns the server-computed total score.

## Professor UI

The Professor Dashboard includes a Project Review Queue with:

- total project count,
- pending count,
- in-review count,
- changes-requested count,
- approved count,
- per-project status and current score,
- direct links to the generic project detail page.

On a project detail page the professor sees the editable rubric form and written feedback field.

## Student UI

The same generic project detail page renders the review read-only for a student. There are no save/reset controls in the student view.

## Security notes

- Shared student JSON remains authoritative for shared project metadata.
- Review state is runtime/private state, similar to auth/session and demo-history data.
- The frontend is not the authorization boundary; backend role checks enforce writes.
- Score ranges are enforced by Pydantic and SQLite CHECK constraints.
- Review writes never invoke project code or shell commands.
- Reviewer identity is derived from the authenticated professor account, not from request payload.
