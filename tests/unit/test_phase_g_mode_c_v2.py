"""Focused PR-C C2 checks: Audit v2 and dormant Mode C dual-path behavior."""
import json
import hashlib
import shutil
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.m8r_05c.audit_package_builder import build_audit_package
from scripts.m8r_05c.canonical import hash_body_excluding_key
from scripts.m8r_05c.citation_builder import CitationIndex
from scripts.m8r_05c.models import CitationToOperationEntry
from scripts.m8r_05c.markdown_renderer import render_result_markdown
from scripts.m8r_05c.models import ProjectionInputs
from server.services.unified_mode_c import (
    _OUTPUT_PATHS, _receipt_calculated_at, ModeCError, build_mode_c_result_package,
)
from scripts.m8r_05c.result_builder import build_result
from scripts.m8r_05c.lineage_resolver import build_lineage_map
from scripts.m8r_05c.citation_builder import build_citation_index


ROOT = Path(__file__).resolve().parents[2]
V1_GOLDEN = ROOT / "tests" / "fixtures" / "phase_g_pr_c" / "v1_mode_c_golden"
V2_ACCEPTANCE = ROOT / "tests" / "fixtures" / "phase_g_pr_c" / "v2_acceptance"


def _inputs() -> ProjectionInputs:
    zeros = "0" * 64
    request = {
        "schema_version": "unified_market_evidence_request.v2",
        "request_id": "umeq-v2-test",
    }
    plan = {
        "plan_id": "umeop-v1-" + "1" * 20,
        "plan_hash": zeros,
        "schema_version": "unified_market_evidence_orchestration_plan.v1",
        "plan_status": "planned",
        "input_bindings": {"f3_validation_output_hash": zeros},
    }
    authorization = {
        "authorization_id": "umea-v1-" + "2" * 20,
        "authorization_hash": zeros,
        "schema_version": "unified_market_evidence_execution_authorization.v1",
    }
    claim = {
        "claim_id": "umecl-v1-" + "3" * 20,
        "schema_version": "unified_market_evidence_consumption_record.v1",
    }
    receipt = {
        "execution_receipt_id": "umerec-v1-" + "4" * 20,
        "execution_receipt_hash": zeros,
        "schema_version": "unified_market_evidence_execution_receipt.v1",
        "overall_status": "succeeded",
        "total_operations": 0,
        "succeeded_operations": 0,
        "failed_operations": 0,
        "finalized_at": "2026-09-20T00:00:00Z",
    }
    bundle = {
        "bundle_id": "umeb-v1-" + "5" * 20,
        "bundle_hash": zeros,
        "schema_version": "unified_market_evidence_bundle.v1",
        "overall_status": "succeeded",
        "total_item_count": 0,
        "finalized_at": "2026-09-20T00:00:00Z",
    }
    return ProjectionInputs(
        request=request,
        f3_validation={},
        plan=plan,
        authorization=authorization,
        consumption_binding={
            "consumption_binding_id": "umecb-v1-" + "6" * 20,
            "consumption_binding_hash": zeros,
        },
        claim=claim,
        receipt=receipt,
        bundle=bundle,
        artifact_root="tests/fixtures",
        calculated_at="2026-09-20T00:00:00Z",
    )


def test_audit_v2_is_deterministic_and_keeps_subordinate_v1_contracts():
    inputs = _inputs()
    body = {
        "schema_version": "unified_market_evidence_result.v2",
        "result_id": "umeresult-v2-" + "a" * 20,
        "request_id": inputs.request["request_id"],
        "result_hash": "0" * 64,
    }
    body["result_hash"] = hash_body_excluding_key(body, "result_hash")
    audit = build_audit_package(
        body, inputs, CitationIndex(), "ai_context/unified_market_evidence_result.v2.json",
        output_schema_version="unified_market_evidence_audit_package.v2",
    )
    schema = json.loads((ROOT / "schemas/unified_market_evidence_audit_package.v2.schema.json").read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(schema).iter_errors(audit))
    assert audit["audit_package_id"].startswith("umeap-v2-")
    assert audit["plan_identity"]["schema_version"].endswith(".v1")
    assert audit["authorization_identity"]["schema_version"].endswith(".v1")
    assert audit["receipt_identity"]["schema_version"].endswith(".v1")
    assert audit == build_audit_package(
        body, inputs, CitationIndex(), "ai_context/unified_market_evidence_result.v2.json",
        output_schema_version="unified_market_evidence_audit_package.v2",
    )


def test_v2_markdown_renders_typed_evidence_without_advice():
    result = {
        "schema_version": "unified_market_evidence_result.v2",
        "result_id": "umeresult-v2-" + "a" * 20,
        "request_id": "request",
        "generated_at": "2026-09-20T00:00:00Z",
        "status": "full_success",
        "request_summary": {"target_count": 1, "requested_data_needs": ["material_disclosures", "monthly_revenue"]},
        "targets": [{"resolution": {"status": "resolved"}, "evidence": {
            "material_disclosures": {"status": "available", "coverage": {"source_report_date": "2026-09-19"}, "source": {"source_family": "MOPS_MATERIAL_DISCLOSURE_OPEN_DATA"}, "items": [{"published_at": "2026-09-19T09:00:00+08:00", "subject": "公告", "description": "說明", "citation_id": "cite-1"}], "citation_ids": ["cite-1"]},
            "monthly_revenue": {"status": "not_yet_available", "coverage": {"reporting_period": "2026-08"}, "value": None, "citation_ids": []},
        }}],
        "audit_reference": {"audit_package_id": "umeap-v2-" + "b" * 20,
                            "schema_version": "unified_market_evidence_audit_package.v2",
                            "relative_path": "audit/unified_market_evidence_audit_package.v2.json"},
    }
    rendered = render_result_markdown(result)
    assert "MOPS_MATERIAL_DISCLOSURE_OPEN_DATA" in rendered
    assert "not_yet_available" in rendered
    assert "unified_market_evidence_audit_package.v2" in rendered
    assert "bullish" not in rendered.lower()
    assert "bearish" not in rendered.lower()


def test_mode_c_version_paths_are_separate_and_unknown_is_rejected():
    assert _OUTPUT_PATHS["unified_market_evidence_result.v1"] != _OUTPUT_PATHS["unified_market_evidence_result.v2"]
    try:
        build_mode_c_result_package({"control_package_id": "umea-v1-test"}, output_schema_version="v9")
    except ModeCError as exc:
        assert exc.code == "unsupported_output_schema_version"
    else:
        raise AssertionError("unknown Mode C output version must fail closed")


def test_mode_c_v2_materializes_in_parallel_without_touching_v1(tmp_path, monkeypatch):
    from server.services import unified_mode_c

    package = tmp_path / "control-package"
    package.mkdir()
    inputs = _inputs()
    calculated_at, calculated_at_source = _receipt_calculated_at(inputs.receipt)
    assert calculated_at == inputs.receipt["finalized_at"]
    assert calculated_at_source == "receipt.finalized_at"
    inputs.calculated_at = calculated_at
    inputs.calculated_at_source = calculated_at_source
    controls = {name: package / f"{name}.json" for name in ("request", "plan", "authorization", "consumption_binding")}
    f3_path = package / "f3.json"
    f3_path.write_text("{}\n", encoding="utf-8")
    paths = (package, controls, package / "claim.json", package / "receipt.json", package / "bundle.json", f3_path)
    monkeypatch.setattr(unified_mode_c, "_load_verified", lambda _control_id: paths)
    monkeypatch.setattr(unified_mode_c, "_f3", lambda *_args: None)
    monkeypatch.setattr(unified_mode_c, "_inputs", lambda *_args: inputs)

    payload = {"control_package_id": "umea-v1-" + "7" * 20}
    first = unified_mode_c.build_mode_c_result_package(payload, output_schema_version="v2")
    second = unified_mode_c.build_mode_c_result_package(payload, output_schema_version="v2")
    assert first["materialization"] == "newly_materialized"
    assert second["materialization"] == "existing_verified"
    assert first["result_id"].startswith("umeresult-v2-")
    assert first["audit_package_id"].startswith("umeap-v2-")
    audit = json.loads((package / _OUTPUT_PATHS["unified_market_evidence_result.v2"][2]).read_text(encoding="utf-8"))
    assert first["canonical_result"]["audit_reference"]["audit_package_id"] == audit["audit_package_id"]
    assert audit["result_id"] == first["canonical_result"]["result_id"]
    assert audit["result_hash"] == first["canonical_result"]["result_hash"]
    assert audit["projector_metadata"]["calculated_at_source"] == "receipt.finalized_at"
    assert (package / _OUTPUT_PATHS["unified_market_evidence_result.v2"][0]).is_file()
    assert not (package / _OUTPUT_PATHS["unified_market_evidence_result.v1"][0]).exists()


def test_historical_v1_outputs_are_byte_immutable_and_override_v2_request(tmp_path, monkeypatch):
    from server.services import unified_mode_c

    package = tmp_path / "control-package"
    package.mkdir()
    inputs = _inputs()
    controls = {name: package / f"{name}.json" for name in ("request", "plan", "authorization", "consumption_binding")}
    f3_path = package / "f3.json"
    f3_path.write_text("{}\n", encoding="utf-8")
    paths = (package, controls, package / "claim.json", package / "receipt.json", package / "bundle.json", f3_path)
    monkeypatch.setattr(unified_mode_c, "_load_verified", lambda _control_id: paths)
    monkeypatch.setattr(unified_mode_c, "_f3", lambda *_args: None)
    monkeypatch.setattr(unified_mode_c, "_inputs", lambda *_args: inputs)
    payload = {"control_package_id": "umea-v1-" + "7" * 20}

    first = unified_mode_c.build_mode_c_result_package(
        payload, output_schema_version="unified_market_evidence_result.v1"
    )
    v1_paths = [package / rel for rel in _OUTPUT_PATHS["unified_market_evidence_result.v1"][:3]]
    before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in v1_paths}
    second = unified_mode_c.build_mode_c_result_package(payload, output_schema_version="v2")
    after = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in v1_paths}

    assert first["output_schema_version"] == "unified_market_evidence_result.v1"
    assert second["output_schema_version"] == "unified_market_evidence_result.v1"
    assert second["materialization"] == "existing_verified"
    assert before == after
    assert not (package / _OUTPUT_PATHS["unified_market_evidence_result.v2"][0]).exists()


def test_repository_v1_golden_reads_verifies_and_preserves_exact_bytes(tmp_path, monkeypatch):
    from server.services import unified_mode_c

    package = tmp_path / "v1-golden"
    shutil.copytree(V1_GOLDEN, package)
    manifest = {}
    for line in (package / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        manifest[relative] = digest
    before = {
        relative: hashlib.sha256((package / relative).read_bytes()).hexdigest()
        for relative in manifest
    }
    assert before == manifest

    inputs = _inputs()
    inputs.request["schema_version"] = "unified_market_evidence_request.v1"
    controls = {name: package / f"{name}.json" for name in ("request", "plan", "authorization", "consumption_binding")}
    paths = (package, controls, package / "claim.json", package / "receipt.json",
             package / "bundle.json", package / "mode_c/f3_validation.json")
    monkeypatch.setattr(unified_mode_c, "_load_verified", lambda _control_id: paths)
    monkeypatch.setattr(unified_mode_c, "_inputs", lambda *_args: inputs)
    payload = {"control_package_id": "umea-v1-" + "7" * 20}
    verified = unified_mode_c.build_mode_c_result_package(payload)
    verified_again = unified_mode_c.build_mode_c_result_package(payload, output_schema_version="v2")
    assert verified["materialization"] == "existing_verified"
    assert verified_again["materialization"] == "existing_verified"
    assert verified["result_id"].startswith("umeresult-v1-")
    assert verified["audit_package_id"].startswith("umeap-v1-")
    assert verified_again["output_schema_version"] == "unified_market_evidence_result.v1"
    assert not (package / _OUTPUT_PATHS["unified_market_evidence_result.v2"][0]).exists()
    after = {
        relative: hashlib.sha256((package / relative).read_bytes()).hexdigest()
        for relative in manifest
    }
    assert after == before


def test_f03_f04_f05_audit_v2_preserves_research_lineage_without_local_paths_or_secrets(tmp_path):
    inputs = _inputs()
    relative = "evidence/phase_g/material-2330.json"
    governed_artifact = {
        "source": {"source_contract_id": "t187ap04_L", "transport": "official_json_openapi",
                   "fallback_used": True},
        "items": [{"raw_speech_time": "93001"}],
    }
    artifact_path = tmp_path / relative
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text(json.dumps(governed_artifact, ensure_ascii=False), encoding="utf-8")
    artifact_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    inputs.plan["operations"] = [{
        "operation_id": "op-g1", "capability_id": "material_disclosures",
        "executor_id": "phase_g_official_research_executor", "market": "TWSE",
        "canonical_target_ids": ["TWSE:2330"],
        "expected_evidence_contract": "phase_g_material_disclosure_operation_evidence.v1",
    }]
    artifact_ref = {
        "relative_path": relative, "sha256": artifact_hash,
        "schema_version": "phase_g_material_disclosure_operation_evidence.v1",
        "byte_size": 321, "item_count": 1,
    }
    inputs.bundle["operation_evidence_entries"] = [{
        "operation_id": "op-g1", "status": "succeeded", "result_item_count": 1,
        "artifacts": [artifact_ref], "warnings": [],
    }]
    inputs.bundle["artifact_inventory"] = [{
        **artifact_ref,
        "evidence_contract": "phase_g_material_disclosure_operation_evidence.v1",
    }]
    inputs.evidence_artifacts[relative] = governed_artifact
    citation_index = CitationIndex(audit_entries=[CitationToOperationEntry(
        citation_id="cite-g1", operation_id="op-g1", capability_id="material_disclosures",
        executor_id="phase_g_official_research_executor", artifact_relative_path=relative,
        artifact_hash=artifact_hash, canonical_target_id="TWSE:2330",
        requested_data_need="material_disclosures",
    )])
    result = {"schema_version": "unified_market_evidence_result.v2",
              "result_id": "umeresult-v2-" + "a" * 20, "request_id": inputs.request["request_id"],
              "result_hash": "0" * 64}
    result["result_hash"] = hash_body_excluding_key(result, "result_hash")
    audit = build_audit_package(
        result, inputs, citation_index, "ai_context/unified_market_evidence_result.v2.json",
        output_schema_version="unified_market_evidence_audit_package.v2",
    )
    lineage = audit["operation_lineage"][0]
    assert lineage["evidence_contract"] == "phase_g_material_disclosure_operation_evidence.v1"
    assert lineage["artifact_references"][0]["sha256"] == artifact_hash
    mapped = audit["citation_to_operation_map"][0]
    assert mapped["canonical_target_id"] == "TWSE:2330"
    resolved_path = tmp_path / mapped["artifact_relative_path"]
    assert hashlib.sha256(resolved_path.read_bytes()).hexdigest() == mapped["artifact_hash"]
    resolved_artifact = json.loads(resolved_path.read_text(encoding="utf-8"))
    assert resolved_artifact["source"] == {
        "source_contract_id": "t187ap04_L", "transport": "official_json_openapi",
        "fallback_used": True,
    }
    assert resolved_artifact["items"][0]["raw_speech_time"] == "93001"
    serialized = json.dumps(audit, ensure_ascii=False)
    assert "D:\\" not in serialized and "file://" not in serialized
    assert all(token not in serialized.lower() for token in ("password", "cookie", "private_key"))


def test_repository_v2_acceptance_samples_validate_and_have_clean_citation_graph():
    manifest = {}
    for line in (V2_ACCEPTANCE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        manifest[name] = digest
    assert all(hashlib.sha256((V2_ACCEPTANCE / name).read_bytes()).hexdigest() == digest
               for name, digest in manifest.items())
    result = json.loads((V2_ACCEPTANCE / "unified_market_evidence_result.v2.json").read_text(encoding="utf-8"))
    audit = json.loads((V2_ACCEPTANCE / "unified_market_evidence_audit_package.v2.json").read_text(encoding="utf-8"))
    result_schema = json.loads((ROOT / "schemas/unified_market_evidence_result.v2.schema.json").read_text(encoding="utf-8"))
    audit_schema = json.loads((ROOT / "schemas/unified_market_evidence_audit_package.v2.schema.json").read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(result_schema).iter_errors(result))
    assert not list(Draft202012Validator(audit_schema).iter_errors(audit))
    emitted = {citation_id for target in result["targets"]
               for evidence in target["evidence"].values()
               for citation_id in evidence.get("citation_ids", [])}
    resolved = {entry["citation_id"] for entry in audit["citation_to_operation_map"]}
    assert emitted == resolved
    assert result["audit_reference"]["audit_package_id"] == audit["audit_package_id"]
    handoff = (V2_ACCEPTANCE / "ai_handoff_snapshot.md").read_text(encoding="utf-8")
    assert handoff == render_result_markdown(result)
    assert "unified_market_evidence_audit_package.v2" in handoff
    assert "audit/unified_market_evidence_audit_package.v2.json" in handoff
    assert "MOPS_MATERIAL_DISCLOSURE_OPEN_DATA" in handoff
    assert "MOPS_MONTHLY_REVENUE_OPEN_DATA" in handoff
    lowered = handoff.lower()
    for forbidden in ("bullish", "bearish", "price target", "目標價", "買進", "賣出"):
        assert forbidden not in lowered


def test_v1_renderer_keeps_v1_audit_label():
    result = json.loads((V1_GOLDEN / "ai_context/unified_market_evidence_result.v1.json").read_text(encoding="utf-8"))
    rendered = render_result_markdown(result)
    assert "unified_market_evidence_audit_package.v1" in rendered
    assert rendered == (V1_GOLDEN / "ai_context/unified_market_evidence_result.v1.md").read_text(encoding="utf-8")
