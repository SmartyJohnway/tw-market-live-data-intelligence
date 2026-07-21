from pathlib import Path
from scripts.m8r_03d_f1_security_master_snapshot_adapter import (
    load_verified_security_master_snapshot,
    ValidatedVerifiedSecurityMasterSnapshot
)

def load_f3_verified_security_master(
    snapshot_path: Path | str,
    manifest_path: Path | str,
    *,
    allow_fixture_snapshot: bool = False,
) -> ValidatedVerifiedSecurityMasterSnapshot:
    """
    Thin wrapper over M8R-03D-F1 strict loader.
    F3 must reuse the existing M8R-03D-F1 verified security-master
    snapshot contract, manifest contract, strict loader, and lookup logic.
    """
    return load_verified_security_master_snapshot(
        snapshot_path,
        manifest_path,
        allow_fixture_snapshot=allow_fixture_snapshot
    )
