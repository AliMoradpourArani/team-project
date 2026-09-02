#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_command git
require_command "$PYTHON_BIN"
require_command npm

if [[ ! -x .venv/bin/python ]]; then
  echo "Creating local environment and installing project dependencies..."
  ./scripts/setup.sh
else
  echo "Using existing .venv."
fi

.venv/bin/python -m backend.database.init_db --seed
.venv/bin/python -m backend.database.sync_data

printf '\n=== Delivery preflight ===\n'
.venv/bin/python -m backend.delivery_preflight --report-only

printf '\n=== Handoff summary ===\n'
printf 'Repository: %s\n' "$(git remote get-url origin 2>/dev/null || echo local-copy)"
printf 'Commit:     %s\n' "$(git rev-parse --short HEAD)"
printf 'Backend:    http://localhost:8000\n'
printf 'Frontend:   http://localhost:5173\n'
printf 'API docs:   http://localhost:8000/docs\n'
printf '\nStart the demo in two terminals:\n'
printf '  .venv/bin/python -m uvicorn backend.app.main:app --reload\n'
printf '  npm run dev --prefix frontend\n'
printf '\nAccounts are local runtime state. If no professor login exists yet, run:\n'
printf '  make auth-bootstrap\n'
printf '\nReview guide: docs/professor-handoff.md\n'
