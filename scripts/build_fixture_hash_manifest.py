"""Build a SHA-256 manifest for fixture files with safe optional output handling."""
from __future__ import annotations
import argparse, json, hashlib
from pathlib import Path

FORBIDDEN_PATH_PARTS = {
    ("frontend", "public"),
    ("research", "generated"),
    ("credentials",),
    ("cookies",),
    ("tokens",),
    ("broker",),
    ("production",),
    ("prod",),
    ("current_market_state",),
}
FORBIDDEN_EXACT = {".env"}


def _parts(path: str | Path) -> tuple[str, ...]:
    raw = str(path).replace("\\", "/")
    return tuple(part for part in raw.split("/") if part and part != ".")


def is_forbidden_output_path(path: str | Path, repo_root: str | Path = ".") -> bool:
    normalized_input = str(path).replace("\\", "/")
    candidate = Path(normalized_input).expanduser()
    root = Path(repo_root).resolve()
    try:
        resolved = candidate.resolve(strict=False)
        rel_parts = resolved.relative_to(root).parts
    except ValueError:
        rel_parts = _parts(path)
    parts = tuple(part.lower() for part in rel_parts)
    if parts and parts[-1] in FORBIDDEN_EXACT:
        return True
    for forbidden in FORBIDDEN_PATH_PARTS:
        n = len(forbidden)
        if any(parts[i:i+n] == forbidden for i in range(0, max(len(parts) - n + 1, 0))):
            return True
    return False


def build_manifest(files: list[str | Path]) -> dict:
    entries = []
    for fixture in files:
        path = Path(fixture)
        entries.append({"path": str(fixture), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    return {"schema_version": "fixture_hash_manifest.v1", "files": entries}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--write-output")
    ap.add_argument("--repo-root", default=".")
    args = ap.parse_args(argv)
    manifest = build_manifest(args.files)
    if args.write_output:
        if is_forbidden_output_path(args.write_output, args.repo_root):
            raise SystemExit("forbidden output path")
        Path(args.write_output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.write_output).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
