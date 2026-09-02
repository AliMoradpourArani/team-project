#!/bin/sh
set -eu

DATA_DIR="/app/data"
SEED_DIR="/app/seed-data"
DB_PATH="${DATABASE_PATH:-/app/data/.runtime/team-project.db}"
PORT_VALUE="${PORT:-8000}"

mkdir -p "$DATA_DIR" "$(dirname "$DB_PATH")"

if [ ! -f "$DATA_DIR/.seeded-from-image" ]; then
  if [ -d "$SEED_DIR" ]; then
    cp -a "$SEED_DIR/." "$DATA_DIR/"
  fi
  touch "$DATA_DIR/.seeded-from-image"
fi

python -m backend.database.init_db --seed

exec uvicorn backend.app.main:app \
  --host 0.0.0.0 \
  --port "$PORT_VALUE" \
  --workers 1 \
  --proxy-headers \
  --forwarded-allow-ips='*'
