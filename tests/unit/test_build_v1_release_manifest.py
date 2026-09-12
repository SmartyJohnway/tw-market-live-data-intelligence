import json

from scripts import build_v1_release_manifest


def test_release_manifest_is_schema_valid_and_bound_to_checked_out_tree() -> None:
    manifest = build_v1_release_manifest.build_manifest(generated_at="2026-09-12T00:00:00Z")
    build_v1_release_manifest.validate_manifest(manifest)
    assert manifest["schema_version"] == "v1_release_manifest.v1"
    assert manifest["product_version"] == "1.0.0-rc.1"
    assert len(manifest["release_commit"]) == 40


def test_release_manifest_cli_writes_only_requested_output(tmp_path) -> None:
    output = tmp_path / "manifest.json"
    assert build_v1_release_manifest.main(["--output", str(output), "--generated-at", "2026-09-12T00:00:00Z"]) == 0
    manifest = json.loads(output.read_text(encoding="utf-8"))
    build_v1_release_manifest.validate_manifest(manifest)
