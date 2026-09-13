import json
import hashlib
import subprocess
from pathlib import Path

import pytest

from scripts import build_v1_release_manifest
from scripts.product_version import product_version


def test_release_manifest_is_schema_valid_and_bound_to_checked_out_tree() -> None:
    manifest = build_v1_release_manifest.build_manifest(generated_at="2026-09-12T00:00:00Z")
    build_v1_release_manifest.validate_manifest(manifest)
    assert manifest["schema_version"] == "v1_release_manifest.v1"
    assert manifest["product_version"] == product_version()
    assert len(manifest["release_commit"]) == 40
    assert manifest["release_tree_sha"] == subprocess.check_output(
        ["git", "rev-parse", "HEAD^{tree}"], text=True
    ).strip()
    for relative, artifact_hash in manifest["artifact_hashes"].items():
        blob = subprocess.check_output(["git", "cat-file", "blob", f"HEAD:{relative}"])
        assert artifact_hash == hashlib.sha256(blob).hexdigest()


def test_release_manifest_hashes_head_blob_not_crlf_checkout_bytes(monkeypatch) -> None:
    relative = "VERSION"
    blob = subprocess.check_output(["git", "cat-file", "blob", f"HEAD:{relative}"])
    original_read_bytes = Path.read_bytes
    monkeypatch.setattr(build_v1_release_manifest, "_git_blob", lambda _: blob)
    monkeypatch.setattr(
        Path,
        "read_bytes",
        lambda self: blob.replace(b"\n", b"\r\n") if self.name == "VERSION" else original_read_bytes(self),
    )
    assert build_v1_release_manifest._governed_artifact_hash(relative) == hashlib.sha256(blob).hexdigest()


def test_release_manifest_rejects_missing_or_untracked_governed_artifact(monkeypatch) -> None:
    monkeypatch.setattr(
        build_v1_release_manifest.subprocess,
        "check_output",
        lambda *args, **kwargs: (_ for _ in ()).throw(subprocess.CalledProcessError(128, args[0])),
    )
    with pytest.raises(RuntimeError, match="not_tracked_in_head"):
        build_v1_release_manifest._git_blob("missing.txt")


def test_release_manifest_cli_writes_only_requested_output(tmp_path) -> None:
    output = tmp_path / "manifest.json"
    assert build_v1_release_manifest.main(["--output", str(output), "--generated-at", "2026-09-12T00:00:00Z"]) == 0
    manifest = json.loads(output.read_text(encoding="utf-8"))
    build_v1_release_manifest.validate_manifest(manifest)
