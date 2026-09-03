# GitHub Sync & In-Page Code Editor

This feature lets a student connect their GitHub account, import one of their
repositories into their ForgeFlow workspace, then edit, run and commit+push the
code directly in the browser. Professors can **view** the imported source and
**run** it, but **cannot edit or push**.

## Roles & access

| Action                        | Student          | Professor                 |
| ----------------------------- | ---------------- | ------------------------- |
| Connect / disconnect GitHub   | Own account only | Forbidden (403)           |
| List & import own repositories| Own account only | Forbidden (403)           |
| Browse project files          | Visible projects | Visible projects (all)    |
| Read a file                   | Visible projects | Visible projects (all)    |
| Write a file                  | Owner only       | Forbidden (403)           |
| Commit + push to GitHub       | Owner only       | Forbidden (403)           |
| Run a project                 | Visible projects | Visible projects (all)    |

"Owner" = the logged-in student's `user_id` equals the project's `user_id`.

## Persistence

- Profile sync: writing `github_username` into `data/users/<id>.json` (then a
  `sync_source_data` pass) links the student in the professor GitHub panel.
- Connection/token: stored in a new SQLite table `github_connections`, which
  lives in the git-ignored `backend/database/dev.db`. Never write a token into
  any tracked file.
- Imported projects follow the existing project contract:
  - metadata: `data/projects/<slug>.json` (`ProjectRecord`)
  - manifest + code: `projects/<owner>/<slug>/project.json` (ProjectManifest:
    `runner: "python-script-v1"`, `entry_point`, `repository_path`) plus the
    repo files. Run `sync_source_data` so the project appears in the DB.

## HTTP API

### `GET /api/github/status`
Student-only. Returns:
```json
{ "connected": false, "username": null, "syncedAt": null, "canPush": false }
```

### `POST /api/github/connect` (CSRF)
Student-only. Body `{ "username": string, "token": string | null }`.
Verifies the username (against GitHub `GET /user` when a token is provided,
otherwise format-validates), persists the connection + optional token in
`github_connections`, syncs `github_username` into the user profile, returns:
```json
{ "connected": true, "username": "octocat", "avatarUrl": null,
  "syncedAt": "2026-09-03T00:00:00Z", "canPush": false }
```

### `POST /api/github/disconnect` (CSRF)
Student-only. Clears the row; returns `{ "connected": false }`.

### `GET /api/github/repos`
Student-only. Lists the student's repositories (authenticated `GET /user/repos`
when a token exists, else public `GET /users/{username}/repos`). Returns array:
```json
[{ "fullName": "octocat/hello", "name": "hello", "owner": "octocat",
   "htmlUrl": "https://github.com/octocat/hello", "language": "Python",
   "defaultBranch": "main", "updatedAt": "...", "private": false }]
```

### `POST /api/github/import` (CSRF)
Student-only. Body `{ "fullName": "octocat/hello" }`. Clones the repository into
`projects/<ownerId>/<slug>/`, writes the metadata + manifest, sets the entry
point to `main.py` (or the first `.py` file), syncs the DB. Returns:
```json
{ "project": { "<ProjectResponse>": null }, "imported": true,
  "repositoryPath": "projects/ali/hello", "entryPoint": "main.py" }
```

### `GET /api/projects/{id}/files`
Visible to student owner + professor. Recursive file listing:
```json
[{ "path": "main.py", "name": "main.py", "isDirectory": false, "size": 13 },
 { "path": "src", "name": "src", "isDirectory": true, "size": 0 }]
```

### `GET /api/projects/{id}/file?path=main.py`
Visible to student owner + professor. Returns `{ "path", "content", "size" }`.

### `PUT /api/projects/{id}/file` (CSRF)
Student owner only. Body `{ "path": "main.py", "content": "..." }`. Returns
`{ "path", "content", "size" }`.

### `POST /api/projects/{id}/commit` (CSRF)
Student owner only. Body `{ "message": "..." }`. Runs `git add -A`,
`git commit`, then `git push` using the stored token's credentials URL against
the project's own remote (`origin`). If no token/canPush, only commit locally
(no push). Returns:
```json
{ "committed": true, "pushed": false, "message": "...", "sha": null, "detail": "..." }
```

## Frontend

- New `GitHubProjectEditor` component (student dashboard):
  - Empty state when not connected / no imported project: message
    "connect to the git first".
  - GitHub connect form + "connect" button; shows connected username when done.
  - Repository picker box (dropdown) + "import" button.
  - File tree + code editor (read/write for student) + run button +
    add-to-activities button + commit/push button.
- Read-only "Source explorer" in `ProjectDetailPage` so professors can browse
  and run code but not edit.
- Every new string must be added to `frontend/src/i18n/translations.ts` for all
  three languages (en, fa, de). Use CSS variables from the existing theme so the
  new UI works in both light and dark mode.