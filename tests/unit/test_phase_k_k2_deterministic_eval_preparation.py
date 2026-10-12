from __future__ import annotations

import hashlib
from pathlib import Path
import shutil

from scripts.prepare_phase_k_k2_deterministic_eval import prepare


def _artifact_hashes(root: Path, manifest: dict) -> dict[str, str]:
    prepared = manifest["generated_package"]["packages"]["success"]
    package = root / prepared["package_path"]
    paths = [
        package / "control" / "manifest.json",
        package / "ai_context" / "unified_market_evidence_result.v3.json",
        package / "audit" / "unified_market_evidence_audit_package.v3.json",
        root / prepared["handoff"]["path"],
    ]
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}


def test_prepare_is_reproducible_isolated_network_free_and_order_flexible(tmp_path: Path):
    first_root = tmp_path / "first"
    first = prepare(first_root)
    first_success_id = first["generated_package"]["packages"]["success"]["control_package_id"]
    first_hashes = _artifact_hashes(first_root, first)
    shutil.rmtree(first_root)
    second = prepare(first_root)

    assert first_success_id == second["generated_package"]["packages"]["success"]["control_package_id"]
    assert first_hashes == _artifact_hashes(first_root, second)
    assert all(value["lineage_verified"] for value in first["generated_package"]["packages"].values())
    assert first["generated_package"]["packages"]["success"]["result_status"] == "full_success"
    assert first["generated_package"]["packages"]["partial"]["result_status"] == "partially_failed"
    assert first["read_only_order_checks"] == {
        "read_then_export": "PASS",
        "export_then_read": "PASS",
        "ordering_precondition_enforced": False,
    }
    assert first["network_counters"] == {
        "market_source_GET": 0,
        "market_source_HEAD": 0,
        "market_source_POST": 0,
        "external_socket_connect_attempts": 0,
        "loopback_test_transport_connects": first["network_counters"]["loopback_test_transport_connects"],
        "fixture_executor_network_required": False,
        "partial_fixture_external_market_network_executed": False,
    }
    assert first["host_evaluation_count"] == 0
    assert first["compatibility_outcome_claims"] == []
    assert len(first["scenario_asset_mapping"]) == 8
    assert len(first["known_preparation_gaps"]) == 1
    assert "K1-05" in first["known_preparation_gaps"][0]
    assert (first_root / "scenario_assets/K1-02/verified_security_master_snapshot_manifest.json").is_file()
    assert (first_root / "scenario_assets/K1-05/snapshot_stale_observations.json").is_file()
    assert (first_root / "scenario_assets/K1-07/unsupported_financial_statements_request.json").is_file()
    assert (first_root / "preparation_manifest.json").is_file()
