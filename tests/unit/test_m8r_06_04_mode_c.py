"""Mode C uses repository-owned, sanitized finalized lineage fixtures only."""
import hashlib
import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.m8r_05c.canonical import hash_body_excluding_key
from scripts.m8r_05c.evidence_projector import _project_envelope
from scripts.m8r_05c.lineage_resolver import OperationBinding
from scripts.m8r_06_01c2_mode_a_security_master_loader import reset_production_mode_a_security_master_for_tests
from server.services import unified_mode_c
from server.services.unified_mode_c import ModeCError, build_mode_c_result_package


FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "m8r_05c"
PACKAGE_ID = "umea-v1-2e589eb14b73fadf6b29"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def reset_mode_a_runtime():
    reset_production_mode_a_security_master_for_tests()
    yield
    reset_production_mode_a_security_master_for_tests()


@pytest.fixture()
def mode_c_root(tmp_path, monkeypatch):
    """Build a sanitized, deterministic finalized package with no live payload."""
    package = tmp_path / "control" / PACKAGE_ID
    control = package / "control"
    control.mkdir(parents=True)
    copies = {
        "request": "request_single_target.json",
        "plan": "plan_single_target.json",
        "authorization": "authorization.json",
        "consumption_binding": "consumption_binding.json",
    }
    for name, source in copies.items():
        shutil.copy2(FIXTURES / source, control / f"{name}.json")
    # These are immutable control members but are not consumed by the 05C projector.
    (control / "preflight.json").write_text("{}", encoding="utf-8")
    (control / "unused_consumption_state.json").write_text("{}", encoding="utf-8")
    hashes = {name: hashlib.sha256((control / f"{name}.json").read_bytes()).hexdigest()
              for name in (*copies, "preflight", "unused_consumption_state")}
    authorization = _load(control / "authorization.json")
    plan = _load(control / "plan.json")
    (control / "manifest.json").write_text(json.dumps({
        "schema_version": "m8r_06_03_control_package.v1",
        "authorization_id": PACKAGE_ID,
        "authorization_hash": authorization["authorization_hash"],
        "plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"],
        "preflight_id": "umeopf-v1-aaaabbbbccccdddd0000", "preflight_hash": "0" * 64,
        "artifact_hashes": hashes,
    }), encoding="utf-8")
    for directory, source in (("claims", "claim.json"), ("receipts", "receipt.json"), ("bundles", "bundle.json")):
        destination = package / directory
        destination.mkdir()
        shutil.copy2(FIXTURES / source, destination / source)
    shutil.copytree(FIXTURES / "artifact_root", package, dirs_exist_ok=True)
    monkeypatch.setattr(unified_mode_c, "CONTROL_ROOT", package.parent)
    monkeypatch.setattr(unified_mode_c, "validate_mode_a_request", lambda _request: _load(FIXTURES / "f3_validation.json"))
    return package


def _build(package: Path) -> dict:
    return build_mode_c_result_package({"control_package_id": PACKAGE_ID})


def test_mode_c_materializes_and_reuses_sanitized_finalized_lineage(mode_c_root):
    result = _build(mode_c_root)
    assert result["result_status"] == "success_with_partial_coverage"
    assert result["external_market_network_executed"] is False
    assert result["materialization"] == "newly_materialized"
    assert (mode_c_root / result["canonical_result_reference"]).is_file()
    assert _build(mode_c_root)["materialization"] == "existing_verified"


@pytest.mark.parametrize("relative", ["claims", "receipts", "bundles"])
def test_mode_c_rejects_missing_final_execution_artifacts(mode_c_root, relative):
    shutil.rmtree(mode_c_root / relative)
    with pytest.raises(ModeCError):
        _build(mode_c_root)


def test_mode_c_rejects_nonfinal_claim(mode_c_root):
    claim = next((mode_c_root / "claims").glob("*.json"))
    data = _load(claim)
    data["state"] = "claimed"
    claim.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ModeCError, match="mode_c_execution_not_finalized"):
        _build(mode_c_root)


def test_mode_c_rejects_evidence_tampering(mode_c_root):
    evidence = next((mode_c_root / "operations").rglob("*.json"))
    evidence.write_text("{}", encoding="utf-8")
    with pytest.raises(ModeCError, match="mode_c_lineage_verification_failed"):
        _build(mode_c_root)


def test_mode_c_rejects_f3_reconstruction_mismatch(mode_c_root, monkeypatch):
    monkeypatch.setattr(unified_mode_c, "validate_mode_a_request", lambda _request: {})
    with pytest.raises(ModeCError, match="mode_c_f3_reconstruction_mismatch"):
        _build(mode_c_root)


def test_existing_result_semantic_tamper_with_rewritten_hash_is_rejected(mode_c_root):
    _build(mode_c_root)
    path = mode_c_root / "ai_context" / "unified_market_evidence_result.v1.json"
    result = _load(path)
    result["request_summary"]["target_count"] = 999
    result["result_hash"] = hash_body_excluding_key(result, "result_hash")
    path.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    (mode_c_root / "ai_context" / "unified_market_evidence_result.v1.md").write_text(
        unified_mode_c.render_result_markdown(result), encoding="utf-8"
    )
    with pytest.raises(ModeCError, match="mode_c_existing_output_inconsistent"):
        _build(mode_c_root)


def test_existing_audit_semantic_tamper_with_rewritten_hash_is_rejected(mode_c_root):
    _build(mode_c_root)
    path = mode_c_root / "audit" / "unified_market_evidence_audit_package.v1.json"
    audit = _load(path)
    audit["warnings"] = ["semantic_tamper"]
    audit["audit_package_hash"] = hash_body_excluding_key(audit, "audit_package_hash")
    path.write_text(json.dumps(audit, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
    with pytest.raises(ModeCError, match="mode_c_existing_output_inconsistent"):
        _build(mode_c_root)


def test_mode_c_rejects_browser_privileged_fields():
    with pytest.raises(ModeCError, match="invalid_api_envelope"):
        build_mode_c_result_package({"control_package_id": PACKAGE_ID, "output_root": "C:/no"})


def test_mode_c_api_rejects_privileged_browser_paths():
    from server.main import app
    response = TestClient(app).post("/api/unified/result-package", json={
        "control_package_id": PACKAGE_ID, "receipt_path": "C:/outside.json"
    })
    assert response.status_code == 422
    assert response.json()["error"] == "invalid_api_envelope"


def test_records_evidence_envelope_is_explicitly_supported():
    binding = OperationBinding(
        operation_id="op", capability_id="current_observation", executor_id="test",
        canonical_target_id="TW.2330", requested_data_need="current_observation",
        market="TWSE", status="succeeded", error_code=None,
        artifact_objects={"evidence": {"schema_version": "m8r_06_03_operation_evidence.v1", "records": [{"price": 1}]}},
    )
    assert _project_envelope(binding, []).observed_fields["price"] == 1


def test_mode_c_browser_state_is_cleared_for_new_authorization_and_displays_summary():
    javascript = (Path("frontend/unified-workbench/unified-workbench.js").read_text(encoding="utf-8"))
    assert "const invalidateModeCState = () =>" in javascript
    assert "// A new authorization must never inherit a prior result package.\n        invalidateModeCState();" in javascript
    assert "result_status:data.result_status, request_summary:data.request_summary" in javascript


def test_verified_handoff_reuses_mode_c_outputs_and_audit_citations(mode_c_root):
    handoff = unified_mode_c.build_mode_c_ai_handoff(PACKAGE_ID)
    result = _build(mode_c_root)
    audit = unified_mode_c.read_mode_c_audit(PACKAGE_ID)
    assert handoff["canonical_result"] == result["canonical_result"]
    assert handoff["ai_ready_markdown"] == result["ai_ready_markdown"]
    assert handoff["audit_package_id"] == audit["audit_package_id"]
    assert handoff["execution_outcome"] == "succeeded"
    assert handoff["additional_market_network_executed"] is False
    assert "external_market_network_executed" not in handoff
    assert handoff["request_mode"] != handoff["execution_outcome"]
    assert handoff["citation_references"] == sorted(
        handoff["citation_references"], key=lambda item: tuple(str(item[key]) for key in (
            "citation_id", "canonical_target_id", "capability_id", "executor_id", "artifact_relative_path", "artifact_hash"
        ))
    )
    serialized = json.dumps(handoff, ensure_ascii=False)
    assert "twse_mis_rich_facts" not in serialized


def test_verified_handoff_rejects_unfinalized_package(mode_c_root):
    claim = next((mode_c_root / "claims").glob("*.json"))
    data = _load(claim)
    data["state"] = "claimed"
    claim.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(ModeCError, match="mode_c_execution_not_finalized"):
        unified_mode_c.build_mode_c_ai_handoff(PACKAGE_ID)
