from __future__ import annotations

from scripts.validate_l5_extension_registration_conformance import load_snapshot, validate_snapshot


def _fixture():
    snapshot = {
        "request_capabilities": ["cap_a"],
        "catalog_capabilities": [{"id": "cap_a", "status": "runtime_executable"}],
        "routes": [{
            "capability_id": "cap_a", "market": "TWSE", "routing_status": "resolved",
            "runtime_executable": True, "selected_executor_id": "exec_a",
            "candidate_executor_ids": ["exec_a"],
        }],
        "executor_metadata": [{"executor_id": "exec_a", "capability_id": "cap_a", "market": "TWSE"}],
        "callable_bindings": [{
            "executor_id": "exec_a", "capability_id": "cap_a", "market": "TWSE",
            "trusted_callable_bound": True, "callable_executor_id": "exec_a",
        }],
        "typed_contract_views": {
            "loader": ["typed_evidence.v1"], "lineage": ["typed_evidence.v1"],
            "projection": ["typed_evidence.v1"], "result": ["typed_evidence.v1"],
            "audit": ["typed_evidence.v1"], "handoff": ["typed_evidence.v1"],
        },
        "schema_contracts": ["typed_evidence.v1"],
        "known_source_ids": ["source_a"],
        "source_bindings": [{"source_id": "source_a", "activation_state": "active", "selected_for_route": True}],
        "derived_catalog_capabilities": ["cap_a"],
        "retained_executor_ids": [],
    }
    checklist = {
        "not_runtime_registry": True, "not_capability_authority": True,
        "not_source_authority": True, "not_dispatch_authority": True,
        "not_plugin_manifest": True, "new_canonical_authorities": 0,
        "runtime_discovery": False,
        "extension_relevant_registration_checks": [{"registration_id": f"row_{i}"} for i in range(30)],
        "not_extension_point_controls": [{"registration_id": f"negative_{i}", "promoted_to_extension_point": False} for i in range(9)],
        "historical_duplication_controls": [{"registration_id": f"historic_{i}", "used_as_current_authority": False} for i in range(2)],
        "friction_group_ids": [f"friction_{i}" for i in range(8)],
    }
    return snapshot, checklist


def _codes(snapshot, checklist):
    return {issue["code"] for issue in validate_snapshot(snapshot, checklist)}


def test_current_explicit_authorities_conform():
    snapshot, checklist = load_snapshot()
    assert validate_snapshot(snapshot, checklist) == []


def test_rejects_unknown_routed_capability():
    snapshot, checklist = _fixture()
    snapshot["routes"][0]["capability_id"] = "unknown_capability"
    assert "A2_UNKNOWN_ROUTED_CAPABILITY" in _codes(snapshot, checklist)


def test_rejects_route_referencing_unknown_executor():
    snapshot, checklist = _fixture()
    snapshot["routes"][0]["selected_executor_id"] = "unknown_executor"
    assert "A2_SELECTED_EXECUTOR_NOT_A_CANDIDATE" in _codes(snapshot, checklist)


def test_rejects_executor_metadata_without_trusted_callable():
    snapshot, checklist = _fixture()
    snapshot["callable_bindings"] = []
    assert "A2_EXECUTOR_WITHOUT_TRUSTED_CALLABLE" in _codes(snapshot, checklist)


def test_rejects_callable_bound_to_unknown_executor_identity():
    snapshot, checklist = _fixture()
    snapshot["callable_bindings"].append({
        "executor_id": "unknown_executor", "capability_id": "cap_a", "market": "TWSE",
        "trusted_callable_bound": True, "callable_executor_id": "unknown_executor",
    })
    assert "A2_CALLABLE_UNKNOWN_EXECUTOR_IDENTITY" in _codes(snapshot, checklist)


def test_rejects_typed_evidence_contract_version_mismatch():
    snapshot, checklist = _fixture()
    snapshot["typed_contract_views"]["lineage"].append("unknown_evidence.v9")
    assert "A2_TYPED_EVIDENCE_CONTRACT_VERSION_MISMATCH" in _codes(snapshot, checklist)


def test_rejects_unknown_source_authority():
    snapshot, checklist = _fixture()
    snapshot["source_bindings"][0]["source_id"] = "unknown_source"
    assert "A2_UNKNOWN_SOURCE_AUTHORITY" in _codes(snapshot, checklist)


def test_rejects_derived_view_disagreeing_with_catalog():
    snapshot, checklist = _fixture()
    snapshot["derived_catalog_capabilities"] = []
    assert "A2_DERIVED_CATALOG_VIEW_MISMATCH" in _codes(snapshot, checklist)


def test_rejects_not_extension_point_promotion():
    snapshot, checklist = _fixture()
    checklist["not_extension_point_controls"][0]["promoted_to_extension_point"] = True
    assert "A2_FORBIDDEN_EXTENSION_POINT_PROMOTION" in _codes(snapshot, checklist)


def test_rejects_historical_duplicate_as_current_authority():
    snapshot, checklist = _fixture()
    checklist["historical_duplication_controls"][0]["used_as_current_authority"] = True
    assert "A2_HISTORICAL_DUPLICATE_AS_CURRENT_AUTHORITY" in _codes(snapshot, checklist)
