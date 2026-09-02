#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

fail() {
  echo "release verification failed: $*" >&2
  exit 1
}

[[ -f VERSION ]] || fail "VERSION is missing"
VERSION="$(tr -d '[:space:]' < VERSION)"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "VERSION must be stable semantic version x.y.z"

NOTES="docs/releases/v${VERSION}.md"
[[ -f "$NOTES" ]] || fail "$NOTES is missing"
[[ -f docs/release-checklist.md ]] || fail "docs/release-checklist.md is missing"
[[ -f scripts/build-release-package.sh ]] || fail "scripts/build-release-package.sh is missing"
[[ -f scripts/tag-release.sh ]] || fail "scripts/tag-release.sh is missing"

bash -n scripts/build-release-package.sh
bash -n scripts/tag-release.sh
bash -n scripts/release-verify.sh

echo "release contract OK: v${VERSION}"
echo "release notes: ${NOTES}"
