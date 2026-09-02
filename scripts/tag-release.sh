#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

fail() {
  echo "release tag blocked: $*" >&2
  exit 1
}

[[ -x .venv/bin/python ]] || fail "local environment missing; run make demo-handoff first"
[[ -f VERSION ]] || fail "VERSION is missing"
VERSION="$(tr -d '[:space:]' < VERSION)"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "VERSION must be stable semantic version x.y.z"
TAG="v${VERSION}"

[[ "$(git branch --show-current)" == "main" ]] || fail "release tags must be created from main"
[[ -z "$(git status --porcelain)" ]] || fail "working tree must be clean"

git fetch --quiet origin main --tags
HEAD_SHA="$(git rev-parse HEAD)"
[[ "$HEAD_SHA" == "$(git rev-parse origin/main)" ]] || fail "local main must exactly match origin/main"
if git rev-parse "$TAG" >/dev/null 2>&1; then
  fail "tag ${TAG} already exists"
fi

./scripts/release-verify.sh
.venv/bin/python -m backend.delivery_preflight

DIST_DIR="dist/release-${TAG}"
ARCHIVE="${DIST_DIR}/team-project-${TAG}.tar.gz"
CHECKSUM="${ARCHIVE}.sha256"
MANIFEST="${DIST_DIR}/release-manifest.json"
[[ -f "$ARCHIVE" && -f "$CHECKSUM" && -f "$MANIFEST" ]] || fail "release package missing; run make release-package first"

EXPECTED_SHA="$(sha256sum "$ARCHIVE" | awk '{print $1}')"
RECORDED_SHA="$(awk '{print $1}' "$CHECKSUM")"
[[ "$EXPECTED_SHA" == "$RECORDED_SHA" ]] || fail "release archive checksum does not match"

readarray -t MANIFEST_VALUES < <(
  .venv/bin/python - "$MANIFEST" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)
print(payload.get("version", ""))
print(payload.get("tag", ""))
print(payload.get("commit", ""))
print(payload.get("sha256", ""))
PY
)
[[ "${MANIFEST_VALUES[0]}" == "$VERSION" ]] || fail "release manifest version does not match VERSION"
[[ "${MANIFEST_VALUES[1]}" == "$TAG" ]] || fail "release manifest tag does not match ${TAG}"
[[ "${MANIFEST_VALUES[2]}" == "$HEAD_SHA" ]] || fail "release package was built from a different commit"
[[ "${MANIFEST_VALUES[3]}" == "$EXPECTED_SHA" ]] || fail "release manifest checksum does not match archive"

git tag -a "$TAG" -m "Team Project ${TAG}"

cat <<EOF
Created local annotated tag ${TAG} at ${HEAD_SHA}.

The tag has NOT been pushed automatically.
Review the package and release checklist, then publish deliberately with:
  git push origin ${TAG}

Release notes:
  docs/releases/${TAG}.md
EOF
