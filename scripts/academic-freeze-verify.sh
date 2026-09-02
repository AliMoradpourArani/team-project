#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

fail() {
  echo "academic freeze verification failed: $*" >&2
  exit 1
}

[[ -x .venv/bin/python ]] || fail "local environment missing; run make demo-handoff first"
[[ -f VERSION ]] || fail "VERSION is missing"
VERSION="$(tr -d '[:space:]' < VERSION)"
TAG="v${VERSION}"
HEAD_SHA="$(git rev-parse HEAD)"

[[ "$(git branch --show-current)" == "main" ]] || fail "freeze verification must run on main"
[[ -z "$(git status --porcelain)" ]] || fail "working tree must be clean"
git fetch --quiet origin main --tags
[[ "$HEAD_SHA" == "$(git rev-parse origin/main)" ]] || fail "local main must exactly match origin/main"

BUNDLE_DIR="dist/academic-submission-${TAG}"
OUTER_ARCHIVE="dist/team-project-academic-submission-${TAG}.tar.gz"
OUTER_CHECKSUM="${OUTER_ARCHIVE}.sha256"
MANIFEST="${BUNDLE_DIR}/academic-submission-manifest.json"

[[ -d "$BUNDLE_DIR" ]] || fail "academic bundle directory missing; run make academic-submission first"
[[ -f "$OUTER_ARCHIVE" && -f "$OUTER_CHECKSUM" ]] || fail "academic bundle archive/checksum missing"
[[ -f "$MANIFEST" && -f "${BUNDLE_DIR}/SHA256SUMS" ]] || fail "academic manifest or SHA256SUMS missing"

EXPECTED_OUTER_SHA="$(sha256sum "$OUTER_ARCHIVE" | awk '{print $1}')"
RECORDED_OUTER_SHA="$(awk '{print $1}' "$OUTER_CHECKSUM")"
[[ "$EXPECTED_OUTER_SHA" == "$RECORDED_OUTER_SHA" ]] || fail "outer academic bundle checksum mismatch"

(
  cd "$BUNDLE_DIR"
  sha256sum -c SHA256SUMS >/dev/null
) || fail "one or more academic bundle files failed SHA-256 verification"

readarray -t VALUES < <(
  .venv/bin/python - "$MANIFEST" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)
print(payload.get("version", ""))
print(payload.get("tagTarget", ""))
print(payload.get("commit", ""))
print("true" if payload.get("preflightReady") is True else "false")
print("true" if payload.get("runtimeStateIncluded") is False else "false")
print("true" if payload.get("credentialsIncluded") is False else "false")
PY
)

[[ "${VALUES[0]}" == "$VERSION" ]] || fail "academic manifest version mismatch"
[[ "${VALUES[1]}" == "$TAG" ]] || fail "academic manifest tag target mismatch"
[[ "${VALUES[2]}" == "$HEAD_SHA" ]] || fail "academic bundle was built from a different commit"
[[ "${VALUES[3]}" == "true" ]] || fail "academic manifest does not record a ready preflight"
[[ "${VALUES[4]}" == "true" ]] || fail "academic manifest reports runtime state inclusion"
[[ "${VALUES[5]}" == "true" ]] || fail "academic manifest reports credential inclusion"

echo "academic freeze verified: ${TAG} @ ${HEAD_SHA}"
