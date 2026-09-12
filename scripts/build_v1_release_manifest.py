#!/usr/bin/env python3
"""Build a deterministic, untagged V1 release-candidate manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import jsonschema

from scripts.product_version import product_version

SCHEMA_PATH = ROOT / "docs/contracts/schemas/v1_release_manifest.v1.schema.json"
DEFAULT_ARTIFACTS = (
    "VERSION",
    "requirements-lock.txt",
    "docs/contracts/v1_public_contracts.json",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git_value(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def build_manifest(*, generated_at: str | None = None) -> dict[str, object]:
    """Return a schema-valid manifest; caller controls its output location."""
    return {
        "schema_version": "v1_release_manifest.v1",
        "product_version": product_version(),
        "release_commit": _git_value("rev-parse", "HEAD"),
        "release_tree_sha": _git_value("rev-parse", "HEAD^{tree}"),
        "artifact_hashes": {relative: _sha256(ROOT / relative) for relative in DEFAULT_ARTIFACTS},
        "generated_at": generated_at
        or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }


def validate_manifest(manifest: object) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(manifest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--generated-at", help="RFC3339 UTC timestamp for deterministic tests")
    args = parser.parse_args(argv)
    manifest = build_manifest(generated_at=args.generated_at)
    validate_manifest(manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "output": str(args.output), "release_commit": manifest["release_commit"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
