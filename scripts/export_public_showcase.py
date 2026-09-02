from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "public-release"
OUTPUT = ROOT / "dist" / "public-showcase"
MANIFEST = SOURCE / "PUBLIC_RELEASE_MANIFEST.json"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    files = manifest["files"]

    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    for name in files:
        source = SOURCE / name
        if not source.is_file():
            raise SystemExit(f"Missing public-release file: {name}")
        target = OUTPUT / name
        shutil.copy2(source, target)
        copied.append(name)

    (OUTPUT / "PUBLIC_RELEASE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    copied.append("PUBLIC_RELEASE_MANIFEST.json")

    print(f"Built {manifest['edition']} v{manifest['version']} with {len(copied)} files")
    for name in copied:
        print(f"- {name}")


if __name__ == "__main__":
    main()
