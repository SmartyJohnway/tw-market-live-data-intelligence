"""A1-D15 explicit-member adapter to existing L2; never discovers or activates.

The destination installation identity is never a restore member. L2 continues
to own package verification, compatibility classification and isolated restore.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from scripts.tw_market_installation import Installation, enumerate_installation_state
from server.services.unified_backup import (
    A1_SETTINGS_BINDING, BackupMember, BackupRoot, plan_backup,
)
from server.services.unified_restore import DEFAULT_COMPATIBILITY_CONTRACT
from server.services.unified_retention_inventory import classify_artifact_family


A1_COMPATIBILITY_CONTRACT = replace(
    DEFAULT_COMPATIBILITY_CONTRACT,
    supported_state_family_versions={
        **DEFAULT_COMPATIBILITY_CONTRACT.supported_state_family_versions,
        "user_product_settings": ("1",),
    },
)


@dataclass(frozen=True)
class DeclaredInstallationMember:
    logical_member_id: str
    role: str
    relative_path: str
    artifact_family: str
    authority_binding_id: str
    expected_sha256: str | None
    source_kind: str = "file"


def installation_backup_plan(installation: Installation, *, members: tuple[DeclaredInstallationMember, ...],
                             backup_tier: str, max_total_bytes: int) -> dict:
    installation.require_initialized()
    roles = {row["role"]: row for row in enumerate_installation_state(installation)}
    roots, declared = {}, []
    allowed = {
        "security_master": {"security_master_active_release_pointer", "security_master_release_history_and_rollback_artifacts"},
        "watchlists": {"persistent_watchlists_and_revision_database"},
        "settings": {"user_product_settings"},
    }
    for item in members:
        role = roles.get(item.role)
        if role is None or not role["portable"] or item.role not in {"settings", "security_master", "watchlists", "governed"}:
            raise ValueError("INSTALLATION_MEMBER_NOT_PORTABLE")
        if item.role == "governed":
            if classify_artifact_family(item.artifact_family)["backup_tier"] != "FULL_GOVERNED":
                raise ValueError("INSTALLATION_MEMBER_FAMILY_MISMATCH")
        elif item.artifact_family not in allowed[item.role]:
            raise ValueError("INSTALLATION_MEMBER_FAMILY_MISMATCH")
        path = Path(role["path"])
        if item.role == "settings":
            if item.relative_path != "settings.json" or item.authority_binding_id != A1_SETTINGS_BINDING:
                raise ValueError("INSTALLATION_SETTINGS_BINDING_REQUIRED")
            root = path.parent
            target = "members/config/settings.json"
        else:
            root = path
            logical_role = {"security_master": "security-master", "watchlists": "watchlists", "governed": "governed"}[item.role]
            target = f"members/state/{logical_role}/{item.relative_path}"
        roots[item.role] = BackupRoot(item.role, root)
        declared.append(BackupMember(item.logical_member_id, item.artifact_family, item.role,
                                    item.relative_path, target, item.authority_binding_id, True,
                                    expected_sha256=item.expected_sha256, source_kind=item.source_kind))
    return plan_backup(backup_tier=backup_tier, roots=tuple(roots.values()), members=declared,
                       source_state_identity=installation.installation_id, max_total_bytes=max_total_bytes)
