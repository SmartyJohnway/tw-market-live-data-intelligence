"""F3's intentionally thin access point to the governed F1 loader."""
from scripts.m8r_03d_f1_security_master_snapshot_adapter import load_verified_security_master_snapshot

def load_f3_verified_security_master(snapshot_path, manifest_path, *, allow_fixture_snapshot=False):
    if not snapshot_path or not manifest_path:
        raise ValueError("explicit_snapshot_and_manifest_paths_required")
    validated = load_verified_security_master_snapshot(snapshot_path, manifest_path, allow_fixture_snapshot=allow_fixture_snapshot)
    if not allow_fixture_snapshot and any((r.get("observation") or {}).get("status") == "fixture_observation_only" for r in validated.snapshot.get("records", [])):
        raise ValueError("fixture_snapshot_rejected_in_production")
    return validated
