from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(run_dir: str | Path) -> list[dict]:
    run_path = Path(run_dir)
    manifest_path = run_path / "sha256_manifest.json"
    errors: list[dict] = []
    if not manifest_path.exists():
        return [{"code": "manifest_missing", "path": str(manifest_path)}]
    try:
        manifest_doc = json.loads(manifest_path.read_text())
    except Exception as exc:
        return [{"code": "manifest_parse_failed", "path": str(manifest_path), "detail": str(exc)}]
    if manifest_doc.get("manifest_final") is not True:
        errors.append({"code": "manifest_not_final", "path": "$.manifest_final"})
    manifest = manifest_doc.get("manifest")
    if not isinstance(manifest, dict):
        errors.append({"code": "manifest_map_missing", "path": "$.manifest"})
        return errors
    for file_name, expected_hash in sorted(manifest.items()):
        path = run_path / file_name
        if not path.exists():
            errors.append({"code": "manifest_artifact_missing", "path": str(path)})
            continue
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            errors.append({"code": "manifest_sha256_mismatch", "path": str(path), "expected": expected_hash, "actual": actual_hash})
    extra = sorted(p.name for p in run_path.glob("*.json") if p.name not in manifest and p.name != "sha256_manifest.json")
    for file_name in extra:
        errors.append({"code": "manifest_untracked_artifact", "path": str(run_path / file_name)})
    return errors


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", required=True)
    args = parser.parse_args(argv)
    errors = verify(args.run_dir)
    print(json.dumps({"ok": not errors, "errors": errors}, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
