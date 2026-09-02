#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

fail() {
  echo "academic submission verification failed: $*" >&2
  exit 1
}

[[ -f VERSION ]] || fail "VERSION is missing"
VERSION="$(tr -d '[:space:]' < VERSION)"
[[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || fail "VERSION must be stable semantic version x.y.z"

[[ -f docs/academic-submission.md ]] || fail "docs/academic-submission.md is missing"
[[ -f docs/repository-freeze.md ]] || fail "docs/repository-freeze.md is missing"
[[ -f docs/professor-handoff.md ]] || fail "docs/professor-handoff.md is missing"
[[ -f "docs/releases/v${VERSION}.md" ]] || fail "release notes for v${VERSION} are missing"
[[ -f scripts/build-academic-submission.sh ]] || fail "scripts/build-academic-submission.sh is missing"
[[ -f scripts/academic-freeze-verify.sh ]] || fail "scripts/academic-freeze-verify.sh is missing"
[[ -f scripts/build-release-package.sh ]] || fail "scripts/build-release-package.sh is missing"
[[ -f scripts/tag-release.sh ]] || fail "scripts/tag-release.sh is missing"

bash -n scripts/academic-submission-verify.sh
bash -n scripts/build-academic-submission.sh
bash -n scripts/academic-freeze-verify.sh
bash -n scripts/build-release-package.sh
bash -n scripts/tag-release.sh
bash scripts/release-verify.sh

echo "academic submission contract OK: v${VERSION}"
