#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

fail() {
  echo "academic submission blocked: $*" >&2
  exit 1
}

[[ -x .venv/bin/python ]] || fail "local environment missing; run make demo-handoff first"
[[ -f VERSION ]] || fail "VERSION is missing"
VERSION="$(tr -d '[:space:]' < VERSION)"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "VERSION must be stable semantic version x.y.z"
TAG="v${VERSION}"

[[ "$(git branch --show-current)" == "main" ]] || fail "official academic bundle must be built from main"
[[ -z "$(git status --porcelain)" ]] || fail "working tree must be clean"

git fetch --quiet origin main --tags
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || fail "local main must exactly match origin/main"

./scripts/academic-submission-verify.sh

PREFLIGHT_TMP="$(mktemp)"
trap 'rm -f "$PREFLIGHT_TMP"' EXIT
.venv/bin/python -m backend.delivery_preflight --json > "$PREFLIGHT_TMP"
.venv/bin/python - <<'PY' "$PREFLIGHT_TMP"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    report = json.load(handle)
if not report.get("releaseCandidateReady"):
    raise SystemExit("academic submission blocked: final delivery preflight is not READY")
PY

./scripts/build-release-package.sh

COMMIT_SHA="$(git rev-parse HEAD)"
COMMIT_DATE="$(git show -s --format=%cI HEAD)"
GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
RELEASE_DIR="dist/release-${TAG}"
RELEASE_ARCHIVE="${RELEASE_DIR}/team-project-${TAG}.tar.gz"
RELEASE_CHECKSUM="${RELEASE_ARCHIVE}.sha256"
RELEASE_MANIFEST="${RELEASE_DIR}/release-manifest.json"

[[ -f "$RELEASE_ARCHIVE" ]] || fail "release archive missing"
[[ -f "$RELEASE_CHECKSUM" ]] || fail "release checksum missing"
[[ -f "$RELEASE_MANIFEST" ]] || fail "release manifest missing"

.venv/bin/python - <<'PY' "$RELEASE_MANIFEST" "$COMMIT_SHA" "$VERSION" "$TAG"
import json
import sys

path, commit, version, tag = sys.argv[1:]
with open(path, encoding="utf-8") as handle:
    manifest = json.load(handle)
if manifest.get("commit") != commit:
    raise SystemExit("academic submission blocked: release manifest commit does not match HEAD")
if manifest.get("version") != version or manifest.get("tag") != tag:
    raise SystemExit("academic submission blocked: release manifest version/tag mismatch")
PY

BUNDLE_DIR="dist/academic-submission-${TAG}"
OUTER_ARCHIVE="dist/team-project-academic-submission-${TAG}.tar.gz"
rm -rf "$BUNDLE_DIR" "$OUTER_ARCHIVE" "${OUTER_ARCHIVE}.sha256"
mkdir -p "$BUNDLE_DIR"

cp "$RELEASE_ARCHIVE" "$BUNDLE_DIR/"
cp "$RELEASE_CHECKSUM" "$BUNDLE_DIR/"
cp "$RELEASE_MANIFEST" "$BUNDLE_DIR/"
cp "$PREFLIGHT_TMP" "$BUNDLE_DIR/preflight.json"
cp docs/professor-handoff.md "$BUNDLE_DIR/PROFESSOR_HANDOFF.md"
cp docs/academic-submission.md "$BUNDLE_DIR/ACADEMIC_SUBMISSION.md"
cp docs/repository-freeze.md "$BUNDLE_DIR/REPOSITORY_FREEZE.md"
cp "docs/releases/${TAG}.md" "$BUNDLE_DIR/RELEASE_NOTES.md"

RELEASE_SHA="$(sha256sum "$RELEASE_ARCHIVE" | awk '{print $1}')"
cat > "$BUNDLE_DIR/academic-submission-manifest.json" <<EOF
{
  "schemaVersion": 1,
  "version": "${VERSION}",
  "tagTarget": "${TAG}",
  "commit": "${COMMIT_SHA}",
  "commitDate": "${COMMIT_DATE}",
  "generatedAt": "${GENERATED_AT}",
  "releaseArchive": "$(basename "$RELEASE_ARCHIVE")",
  "releaseArchiveSha256": "${RELEASE_SHA}",
  "preflightReady": true,
  "runtimeStateIncluded": false,
  "credentialsIncluded": false,
  "sourcePolicy": "tracked source only via Phase 13 release package"
}
EOF

(
  cd "$BUNDLE_DIR"
  sha256sum \
    "$(basename "$RELEASE_ARCHIVE")" \
    "$(basename "$RELEASE_CHECKSUM")" \
    release-manifest.json \
    preflight.json \
    PROFESSOR_HANDOFF.md \
    ACADEMIC_SUBMISSION.md \
    REPOSITORY_FREEZE.md \
    RELEASE_NOTES.md \
    academic-submission-manifest.json > SHA256SUMS
)

tar -C "$(dirname "$BUNDLE_DIR")" -czf "$OUTER_ARCHIVE" "$(basename "$BUNDLE_DIR")"
OUTER_SHA="$(sha256sum "$OUTER_ARCHIVE" | awk '{print $1}')"
printf '%s  %s\n' "$OUTER_SHA" "$(basename "$OUTER_ARCHIVE")" > "${OUTER_ARCHIVE}.sha256"

cat <<EOF

Academic submission bundle ready: ${TAG}
  bundle:    ${OUTER_ARCHIVE}
  checksum:  ${OUTER_ARCHIVE}.sha256
  directory: ${BUNDLE_DIR}
  commit:    ${COMMIT_SHA}

The bundle contains the tracked-source release artifact, immutable checksums, final preflight report,
professor handoff instructions, release notes, and repository freeze policy.
Runtime SQLite, sessions, passwords, tokens, .env files, and local caches are excluded.
EOF
