# Rich project demos

Phase 7 expands member-project integration without expanding arbitrary code execution.

## Supported contracts

| Project type | Runner | Demo mode | Entry point | Starts a process? |
| --- | --- | --- | --- | --- |
| `cli` | `python-script-v1` | execute | `.py` | yes, opt-in |
| `static-web` | `static-site-v1` | preview | `.html` / `.htm` | no |
| `api` | `openapi-json-v1` | preview | `.json` | no |

The `project_type` and `runner` values are paired. A mismatched pair is rejected by manifest validation.

## Static web preview

Static HTML is read as bounded UTF-8 text and returned as preview data. The React UI renders it in an iframe with an empty sandbox and an injected restrictive Content Security Policy.

The preview policy does not grant scripts, forms, network connections, nested frames, base URL changes, or navigation. Inline CSS and data-image assets are allowed so simple self-contained student demos remain visible.

The static preview is a presentation feature, not a production web host.

## OpenAPI preview

API projects use a checked-in OpenAPI 3.x JSON document rather than starting an HTTP server. The backend validates:

- JSON object structure,
- OpenAPI version beginning with `3.`,
- a top-level `paths` object,
- optional `info` object shape,
- source and normalized preview size limits.

The normalized contract is displayed as text in the project detail page.

## Executed Python demos

`python-script-v1` remains the only local process runner. It keeps the Phase 5 security boundary:

- explicit `PROJECT_RUNNER_ENABLED=true`,
- server-derived argv,
- `shell=False`,
- project-directory confinement,
- symlink rejection,
- bounded timeout and output,
- reviewed repository code only.

Preview-only projects cannot call the local process runner, even when the runner feature flag is enabled.

## Why API servers are not started automatically

Starting arbitrary member web/API servers would introduce port allocation, lifecycle management, network exposure, dependency installation, and a much larger isolation problem. Phase 7 deliberately previews API contracts instead. A future isolated service runner should use a dedicated container/sandbox boundary rather than extending the backend process privileges.
