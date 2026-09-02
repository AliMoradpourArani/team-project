#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

fail() {
  echo "release package blocked: $*" >&2
  exit 1
}

[[ -x .venv/bin/python ]] || fail "local environment missing; run make demo-handoff first"
[[ -f VERSION ]] || fail "VERSION is missing"
VERSION="$(tr -d '[:space:]' < VERSION)"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "VERSION must be stable semantic version x.y.z"
TAG="v${VERSION}"

CURRENT_BRANCH="$(git branch --show-current)"
[[ "$CURRENT_BRANCH" == "main" ]] || fail "build the official package from main, not ${CURRENT_BRANCH:-detached HEAD}"
[[ -z "$(git status --porcelain)" ]] || fail "working tree must be clean"

./scripts/release-verify.sh
.venv/bin/python -m backend.delivery_preflight

COMMIT_SHA="$(git rev-parse HEAD)"
COMMIT_DATE="$(git show -s --format=%cI HEAD)"
PREFIX="team-project-${TAG}/"
DIST_DIR="dist/release-${TAG}"
ARCHIVE="${DIST_DIR}/team-project-${TAG}.tar.gz"
CHECKSUM="${ARCHIVE}.sha256"
MANIFEST="${DIST_DIR}/release-manifest.json"

rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

git archive --format=tar --prefix="$PREFIX" HEAD | gzip -n > "$ARCHIVE"
ARCHIVE_SHA="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
printf '%s  %s\n' "$ARCHIVE_SHA" "$(basename "$ARCHIVE")" > "$CHECKSUM"

cat > "$MANIFEST" <<EOF
{
  "schemaVersion": 1,
  "version": "${VERSION}",
  "tag": "${TAG}",
  "commit": "${COMMIT_SHA}",
  "commitDate": "${COMMIT_DATE}",
  "archive": "$(basename "$ARCHIVE")",
  "sha256": "${ARCHIVE_SHA}",
  "source": "git archive of tracked files only",
  "runtimeStateIncluded": false
}
EOF

cat <<EOF

Release package ready: ${TAG}
  archive:  ${ARCHIVE}
  checksum: ${CHECKSUM}
  manifest: ${MANIFEST}
  commit:   ${COMMIT_SHA}

Runtime SQLite, sessions, passwords, tokens, local environment files, and ignored build output are not included.
Next: inspect docs/release-checklist.md, then run make release-tag.
EOF
