from __future__ import annotations

import hashlib
import json
import socket
import sqlite3
from pathlib import Path

from server.services.unified_retention_inventory import (
    classify_artifact,
    classify_artifact_family,
    retention_inventory,
)


def _tree_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_registry_has_deterministic_complete_bounded_rows() -> None:
    rows = retention_inventory()
    assert rows == retention_inventory()
    assert len({row["artifact_family"] for row in rows}) == len(rows)
    required = {
        "artifact_family", "state_class", "authority_role", "replay_required",
        "audit_required", "rebuildable", "network_required_to_rebuild",
        "current_mutable_authority_required_to_rebuild", "deletion_eligible",
        "deletion_prerequisites", "backup_tier", "integrity_binding", "notes",
    }
    assert all(set(row) == required for row in rows)
    assert all(row["deletion_eligible"] != "POTENTIALLY_ELIGIBLE" or row["deletion_prerequisites"] for row in rows)


def test_registry_uses_only_bounded_policy_vocabulary() -> None:
    rows = retention_inventory()
    assert {row["state_class"] for row in rows} <= {
        "CANONICAL_USER_STATE", "GOVERNED_EVIDENCE", "REBUILDABLE_DERIVED",
        "EPHEMERAL", "UNCLASSIFIED_REQUIRES_POLICY",
    }
    assert {row["rebuildable"] for row in rows} <= {
        "NOT_REBUILDABLE", "DETERMINISTIC_FROM_RETAINED_AUTHORITY",
        "REQUIRES_CURRENT_MUTABLE_AUTHORITY", "REQUIRES_REFETCH", "UNKNOWN",
    }
    bounded_fact = {"YES", "NO", "CONDITIONAL", "UNKNOWN"}
    for key in ("replay_required", "audit_required", "network_required_to_rebuild", "current_mutable_authority_required_to_rebuild"):
        assert {row[key] for row in rows} <= bounded_fact
    assert {row["deletion_eligible"] for row in rows} <= {
        "PROHIBITED", "NOT_YET_ELIGIBLE", "POTENTIALLY_ELIGIBLE", "EPHEMERAL",
    }
    assert {row["backup_tier"] for row in rows} <= {"CORE", "FULL_GOVERNED", "DERIVED", "NONE", "UNDETERMINED"}


def test_required_governed_families_are_protected() -> None:
    for family in (
        "finalized_control_package", "f3_historical_validation_artifact",
        "persisted_result_json", "persisted_result_markdown", "persisted_audit_package",
        "selection_provenance", "operation_evidence_and_source_snapshots",
    ):
        row = classify_artifact_family(family)
        assert row["state_class"] == "GOVERNED_EVIDENCE"
        assert row["deletion_eligible"] in {"PROHIBITED", "NOT_YET_ELIGIBLE"}
    f3 = classify_artifact_family("f3_historical_validation_artifact")
    assert f3["replay_required"] == "YES"
    assert f3["rebuildable"] == "NOT_REBUILDABLE"


def test_unknown_and_unbound_artifacts_fail_closed() -> None:
    assert classify_artifact_family("mystery_artifact")["state_class"] == "UNCLASSIFIED_REQUIRES_POLICY"
    assert classify_artifact()["state_class"] == "UNCLASSIFIED_REQUIRES_POLICY"
    assert classify_artifact(artifact_family="operational_jsonl_diagnostics")["state_class"] == "UNCLASSIFIED_REQUIRES_POLICY"
    assert classify_artifact(
        artifact_family="operational_jsonl_diagnostics",
        authority_binding_verified=True,
        governed_reference_found=True,
    )["state_class"] == "UNCLASSIFIED_REQUIRES_POLICY"
    assert classify_artifact(
        artifact_family="operational_jsonl_diagnostics",
        authority_binding_verified=True,
        governed_reference_found=False,
    )["state_class"] == "EPHEMERAL"


def test_ephemeral_families_require_positive_ownership_and_no_governed_reference() -> None:
    for family in ("preview_only_temporary_material", "temporary_test_acceptance_runtime", "lifecycle_ownership_runtime_files"):
        row = classify_artifact_family(family)
        assert row["deletion_eligible"] == "EPHEMERAL"
        assert row["rebuildable"] == "UNKNOWN"
        assert classify_artifact(artifact_family=family, authority_binding_verified=True)["state_class"] == "UNCLASSIFIED_REQUIRES_POLICY"
        assert classify_artifact(artifact_family=family, authority_binding_verified=True, governed_reference_found=False)["state_class"] == "EPHEMERAL"


def test_classifier_has_zero_filesystem_sqlite_and_network_effects(tmp_path: Path, monkeypatch) -> None:
    sentinel = tmp_path / "retained.json"
    sentinel.write_text(json.dumps({"authority": "test", "value": 7}), encoding="utf-8")
    before = _tree_snapshot(tmp_path)
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("classifier attempted an external or database operation")

    monkeypatch.setattr(sqlite3, "connect", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    assert classify_artifact_family("persisted_audit_package")["audit_required"] == "YES"
    assert classify_artifact(artifact_family="cache", authority_binding_verified=True)["state_class"] == "UNCLASSIFIED_REQUIRES_POLICY"
    assert calls == []
    assert _tree_snapshot(tmp_path) == before
