from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "public-release"
MANIFEST = PUBLIC / "PUBLIC_RELEASE_MANIFEST.json"


def test_public_release_manifest_is_complete() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["version"] == "0.13.0"
    assert data["edition"] == "community-showcase"
    assert data["files"]
    for name in data["files"]:
        assert "/" not in name
        assert "\\" not in name
        assert (PUBLIC / name).is_file()


def test_public_release_contains_expected_policy_docs() -> None:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = set(data["files"])
    assert {"README.md", "ARCHITECTURE.md", "FEATURES.md", "SECURITY.md", "RELEASE_NOTES.md", "LICENSE"} <= files
