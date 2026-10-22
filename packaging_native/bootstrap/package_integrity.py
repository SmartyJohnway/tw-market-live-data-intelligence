"""Standard-library package integrity verification for the native distribution."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any

MANIFEST_NAME = "distribution-manifest.json"
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_RESERVED = {"con", "prn", "aux", "nul", "conin$", "conout$", *(f"com{i}" for i in "123456789¹²³"), *(f"lpt{i}" for i in "123456789¹²³")}
_TOP_KEYS = {"schema_version", "product_name", "product_version", "source_commit", "source_tree", "target_os", "target_arch", "python_requirement", "package_profile", "member_count", "members", "manifest_canonical_sha256"}
_MEMBER_KEYS = {"relative_path", "role", "bytes", "sha256"}


def _fail(message: str) -> None:
    raise ValueError(f"package_integrity_failed: {message}")


def _canonical_without_digest(manifest: dict[str, Any]) -> bytes:
    copy = dict(manifest)
    copy.pop("manifest_canonical_sha256", None)
    return json.dumps(copy, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_digest(manifest: dict[str, Any]) -> str:
    """Return the canonical SHA-256 digest of a manifest without its self field."""
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    return hashlib.sha256(_canonical_without_digest(manifest)).hexdigest()


def _safe_relative(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        _fail("invalid relative path")
    if value.startswith(("/", "\\")) or ":" in value:
        _fail("absolute or drive-qualified path")
    parts = value.split("/")
    if any(p in ("", ".", "..") for p in parts):
        _fail("path traversal or empty component")
    for part in parts:
        if any(ord(c) < 32 or c in '<>"|?*' for c in part) or part.endswith((".", " ")):
            _fail("unsafe path component")
        stem = part.split(".", 1)[0].casefold()
        if stem in _RESERVED:
            _fail("reserved Windows name")
    return value


def _reparse(path: Path) -> bool:
    try:
        junction = getattr(path, "is_junction", lambda: False)()
        attrs = getattr(path.lstat(), "st_file_attributes", 0)
        return path.is_symlink() or junction or bool(attrs & 0x400)
    except (OSError, AttributeError):
        return True


def _check_components(root: Path, rel: str) -> None:
    current = root
    for component in rel.split("/"):
        current = current / component
        if _reparse(current):
            _fail(f"reparse point: {rel}")


def verify_bundle(root: str | os.PathLike[str]) -> dict[str, Any]:
    """Verify a bundle and return its validated manifest; failures are fail-closed."""
    bundle = Path(root)
    if not bundle.is_absolute() or not bundle.is_dir() or _reparse(bundle):
        _fail("bundle root unavailable or reparse point")
    current = bundle
    for _ in range(len(bundle.parts)):
        if _reparse(current):
            _fail("bundle ancestor reparse point")
        if current.parent == current: break
        current = current.parent
    bundle = bundle.resolve()
    manifest_path = bundle / MANIFEST_NAME
    if _reparse(manifest_path):
        _fail("manifest reparse point")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        _fail(f"manifest unreadable: {exc}")
    if not isinstance(manifest, dict) or set(manifest) != _TOP_KEYS:
        _fail("manifest schema keys")
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1 or manifest.get("product_name") != "TW-Market":
        _fail("unsupported schema or product")
    for key in ("product_version", "source_commit", "source_tree", "target_os", "target_arch", "python_requirement", "package_profile"):
        if not isinstance(manifest.get(key), str) or not manifest[key]:
            _fail(f"invalid {key}")
    if not _HEX40.fullmatch(manifest["source_commit"]) or not _HEX40.fullmatch(manifest["source_tree"]):
        _fail("invalid source identity")
    if type(manifest.get("member_count")) is not int or manifest["member_count"] < 0:
        _fail("invalid member_count")
    members = manifest.get("members")
    if not isinstance(members, list) or manifest["member_count"] != len(members):
        _fail("member count mismatch")
    digest = manifest.get("manifest_canonical_sha256")
    if not isinstance(digest, str) or not _HEX64.fullmatch(digest) or digest != canonical_digest(manifest):
        _fail("manifest self hash mismatch")
    seen: set[str] = set()
    listed: set[str] = set()
    for member in members:
        if not isinstance(member, dict) or set(member) != _MEMBER_KEYS:
            _fail("member schema")
        rel = _safe_relative(member["relative_path"])
        folded = rel.casefold()
        if folded == MANIFEST_NAME or folded.split('/')[0] == 'runtime':
            _fail("protected path listed as member")
        if folded in seen:
            _fail("duplicate member path")
        seen.add(folded); listed.add(rel)
        if member["role"] not in {"application", "runtime_resource", "bootstrap", "launcher", "dependency", "license", "metadata"}:
            _fail("invalid member role")
        if type(member["bytes"]) is not int or member["bytes"] < 0 or not isinstance(member["sha256"], str) or not _HEX64.fullmatch(member["sha256"]):
            _fail("invalid member digest metadata")
        _check_components(bundle, rel)
        target = bundle / Path(rel)
        if not target.is_file() or _reparse(target):
            _fail(f"missing or reparse member: {rel}")
        if target.stat().st_size != member["bytes"]:
            _fail(f"size mismatch: {rel}")
        h = hashlib.sha256()
        with target.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                h.update(chunk)
        if h.hexdigest() != member["sha256"]:
            _fail(f"hash mismatch: {rel}")
        if rel.casefold() in {MANIFEST_NAME.casefold(), "runtime", "runtime/"}:
            _fail("protected path listed as member")
    # Every payload file must be manifested, except rebuildable runtime contents.
    allowed_dirs = {str(parent).replace('\\', '/').casefold()
                    for item in listed for parent in Path(item).parents if str(parent) != '.'}
    for parent, dirs, files in os.walk(bundle, followlinks=False):
        for name in dirs + files:
            path = Path(parent) / name
            rel = path.relative_to(bundle).as_posix()
            if _reparse(path):
                _fail(f"reparse point: {rel}")
            if rel == 'runtime' or rel.startswith('runtime/'):
                continue
            if path.is_dir():
                if rel.casefold() not in allowed_dirs:
                    _fail(f"unexpected directory: {rel}")
            elif rel != MANIFEST_NAME and rel.casefold() not in seen:
                _fail(f"unexpected unmanifested file: {rel}")
    return {"status": "verified", "bundle_root": str(bundle), "manifest": manifest, "manifest_canonical_sha256": digest}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        print(json.dumps(verify_bundle(args.root), sort_keys=True, ensure_ascii=False))
    except ValueError as exc:
        print(str(exc), file=__import__("sys").stderr)
        raise SystemExit(1)
