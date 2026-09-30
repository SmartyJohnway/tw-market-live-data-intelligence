from __future__ import annotations

import hashlib
import copy
import json
from pathlib import Path

import jsonschema
import pytest

from server.services.phase_i_i2_index_futures_adapters import (
    MAX_RESPONSE_BYTES,
    MAX_ROOT_ROWS,
    I2SourceError,
    alignment_status,
    decode_taifex_payload,
    normalize_taifex_tx_payload,
    select_tx_regular_series,
)
from server.services.phase_i_i2_offline_candidate import (
    EXECUTOR_ID,
    build_i2_candidate_runtime_adapter_registry,
    run_i2_candidate_offline_batch,
)
from scripts.m8r_05c.audit_package_builder import build_audit_package
from scripts.m8r_05c.citation_builder import build_citation_index
from scripts.m8r_05c.lineage_resolver import build_lineage_map
from scripts.m8r_05c.models import ProjectionInputs
from scripts.m8r_05c.result_builder import build_result

ROOT = Path(__file__).resolve().parents[2]
STAMP = "2026-09-30T02:00:00Z"
TRANSPORT_STAMP = "2026-09-30T02:00:01Z"


def row(**changes):
    value = {
        "Date": "20260929", "Contract": "TX", "ContractMonth(Week)": "202610",
        "Open": "48098", "High": "48194", "Low": "47630", "Last": "47767",
        "Change": "-358", "%": "-0.74%", "Volume": "43812",
        "SettlementPrice": "47781", "OpenInterest": "102023", "BestBid": "47753",
        "BestAsk": "47765", "TradingHalt": "", "TradingSession": "一般",
    }
    value.update(changes)
    return value


def evidence(rows, *, transport=None, cite="cite-fixture"):
    return normalize_taifex_tx_payload(
        rows, governed_retrieved_at=STAMP, fmtqik_benchmark_date="2026-09-29",
        citation_ids=[cite], transport=transport,
    )


def schema_validate(value):
    schema = json.loads((ROOT / "schemas/index_futures_context_evidence.v1.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(value)


def test_date_and_nearest_series_selection_is_frozen_and_deterministic():
    values = [
        row(**{"ContractMonth(Week)": "202610"}),
        row(**{"ContractMonth(Week)": "202612"}),
        row(**{"ContractMonth(Week)": "202611"}),
        row(**{"ContractMonth(Week)": "202610/202611"}),
        row(**{"ContractMonth(Week)": "202613"}),
        row(**{"ContractMonth(Week)": "202610W1"}),
        row(**{"TradingSession": "盤後"}),
        row(**{"Contract": "MTX"}),
    ]
    status, period, official_date, selected = select_tx_regular_series(values)
    assert (status, period, official_date.isoformat(), selected["TradingSession"]) == ("selected", "202610", "2026-09-29", "一般")


def test_latest_valid_source_date_does_not_fallback_to_older_eligible_date():
    rows = [row(**{"Date": "20260929"}), row(**{"Date": "20260930", "Contract": "MTX"})]
    assert select_tx_regular_series(rows)[:3] == ("unavailable", None, __import__("datetime").date(2026, 9, 30))
    assert select_tx_regular_series([row(**{"Date": "20260230"})])[0] == "source_failed"
    assert select_tx_regular_series([row(**{"Date": "民國1150101"})])[0] == "source_failed"


def test_duplicate_nearest_binding_fails_closed():
    assert select_tx_regular_series([row(), row()])[0] == "binding_failed"
    duplicate = evidence([row(), row()])
    schema_validate(duplicate)
    assert duplicate["status"] == "binding_failed"


def test_no_eligible_contract_is_unavailable_without_older_date_fallback():
    value = evidence([row(**{"Date":"20260929"}), row(**{"Date":"20260930", "Contract":"MTX"})])
    schema_validate(value)
    assert value["status"] == "unavailable"
    assert value["trade_date"] == "2026-09-30"
    assert value["alignment_status"] == "unavailable"


def test_complete_normalization_units_and_alignment_validate():
    value = evidence([row()])
    schema_validate(value)
    assert value["status"] == "complete"
    assert value["market_data"]["change_percent"] == -0.74
    assert value["unit_metadata"]["change_percent"] == "percent"
    assert value["alignment_status"] == "same_trade_date_non_simultaneous_close"
    assert value["currentness_status"] == "unknown"
    assert value["retrieved_at"] == STAMP


@pytest.mark.parametrize("marker", ["-", "NULL", ""])
def test_governed_missing_marker_is_partial_not_zero(marker):
    value = evidence([row(Open=marker)])
    schema_validate(value)
    assert value["status"] == "partial"
    assert "open" in value["missing_fields"]
    assert "open" not in value["market_data"]


def test_best_bid_ask_are_optional_nullable_observations():
    value = evidence([row(BestBid="-", BestAsk="NULL")])
    schema_validate(value)
    assert value["status"] == "complete"
    assert value["market_data"]["best_bid"] is None
    assert value["market_data"]["best_ask"] is None


def test_partial_with_no_observed_numeric_value_fails_closed():
    empty_row = row(**{"Open":"-","High":"-","Low":"-","Last":"-","Change":"-","%":"-",
                       "Volume":"-","SettlementPrice":"-","OpenInterest":"-","BestBid":"-","BestAsk":"-"})
    value = evidence([empty_row])
    schema_validate(value)
    assert value["status"] == "source_failed"
    assert "market_data" not in value


@pytest.mark.parametrize("field,value", [("Volume", "-1"), ("OpenInterest", "-1"), ("Last", "NaN"), ("Open", "bad")])
def test_malformed_or_invalid_numeric_is_source_failed(field, value):
    normalized = evidence([row(**{field: value})])
    schema_validate(normalized)
    assert normalized["status"] == "source_failed"
    assert "market_data" not in normalized


def test_selected_row_missing_structural_key_and_non_json_numeric_fail_closed():
    malformed = row()
    del malformed["Open"]
    value = evidence([malformed])
    schema_validate(value)
    assert value["status"] == "source_failed"
    payload = json.dumps([row(High=float("nan"))], allow_nan=True).encode()
    non_json_numeric = normalize_taifex_tx_payload(payload, governed_retrieved_at=STAMP,
        fmtqik_benchmark_date=None, citation_ids=["cite-nan"])
    schema_validate(non_json_numeric)
    assert non_json_numeric["status"] == "source_failed"


def test_payload_decoder_enforces_utf8_json_array_and_resource_bounds():
    assert decode_taifex_payload(b"\xff[]")[1] == "source_failed:invalid_utf8_or_json"
    assert decode_taifex_payload(b"{}")[1] == "source_failed:root_not_array"
    assert decode_taifex_payload(b"not-json")[1] == "source_failed:invalid_utf8_or_json"
    assert decode_taifex_payload(b" " * (MAX_RESPONSE_BYTES + 1))[1] == "source_failed:response_too_large"
    too_many = json.dumps([row()] * (MAX_ROOT_ROWS + 1)).encode()
    assert decode_taifex_payload(too_many)[1] == "source_failed:too_many_rows"
    assert decode_taifex_payload(json.dumps([None]).encode())[1] == "source_failed:row_not_object"


def test_alignment_only_uses_supplied_fmtqik_date():
    assert alignment_status("complete", "2026-09-29", None) == "not_comparable"
    assert alignment_status("partial", "2026-09-29", "2026-09-30") == "different_trade_date"
    assert alignment_status("unavailable", None, "2026-09-29") == "unavailable"


def _execution_request(target_id, operation_id, request_id):
    return {
        "schema_version": "unified_market_evidence_execution_request.v2",
        "execution_request_id": request_id,
        "execution_request_hash": hashlib.sha256(request_id.encode()).hexdigest(),
        "operation_id": operation_id,
        "batch_group_id": "umeop-batch-v1-" + "b" * 20,
        "plan_id": "plan-fixture", "plan_hash": "a" * 64,
        "authorization_id": "umea-v1-" + "a" * 20, "authorization_hash": "c" * 64,
        "consumption_binding_id": "umeacb-v1-" + "d" * 20, "consumption_binding_hash": "e" * 64,
        "market": "TWSE", "approved_security_identifiers": [target_id],
        "approved_security_types": ["company_share", "common_share"],
        "capability_id": "index_futures_context", "executor_id": EXECUTOR_ID,
        "requested_fields": [], "currentness_requirement": None, "maximum_records": 1,
        "timeout_seconds": 30, "network_authorized": False,
        "relative_contained_output_path": f"operations/{operation_id}.execution-request.json",
        "parameters": {},
    }


def test_candidate_batch_reuses_one_injected_source_and_emits_v2_artifact_lineage():
    operation_ids = ["umeop-op-v1-" + c * 20 for c in "123"]
    request_ids = ["umereq-v2-" + c * 20 for c in "456"]
    targets = []
    for code, operation_id, request_id in zip(("1101", "1102", "2330"), operation_ids, request_ids):
        canonical_id = f"TWSE:{code}"
        targets.append({
            "canonical_target_id": canonical_id, "market": "TWSE",
            "instrument_family": "company_share", "instrument_type": "common_share",
            "operation_id": operation_id, "execution_request_id": request_id,
            "execution_request_hash": hashlib.sha256(request_id.encode()).hexdigest(),
            "execution_request": _execution_request(canonical_id, operation_id, request_id),
        })
    payload = json.dumps([row()], separators=(",", ":")).encode()
    result = run_i2_candidate_offline_batch(targets, source_payload=payload, governed_retrieved_at=STAMP,
                                            transport_retrieved_at=TRANSPORT_STAMP,
                                            fmtqik_benchmark_date="2026-09-29")
    assert result["network_calls"] == 0 and result["retry_count"] == 0
    assert result["simulated_source_acquisition_count"] == 1
    assert len(result["operation_results"]) == 3
    assert all(item["schema_version"] == "unified_market_evidence_operation_result.v2" for item in result["operation_results"])
    assert len(result["artifact_bytes"]) == 3
    for result_entry in result["operation_results"]:
        art = result_entry["evidence_artifacts"][0]
        body = result["artifact_bytes"][art["relative_path"]]
        evidence_value = json.loads(body)
        schema_validate(evidence_value)
        assert evidence_value["citation_ids"]
        assert art["sha256"] == hashlib.sha256(body).hexdigest()
        assert art["artifact_role"] == "primary_evidence"
        assert payload not in body
        assert json.loads(body)["transport"]["retrieved_at"] == TRANSPORT_STAMP
        assert json.loads(body)["retrieved_at"] == STAMP


def test_candidate_rejects_tpex_and_never_uses_normal_production_registry():
    registry = build_i2_candidate_runtime_adapter_registry()
    assert set(registry) == {(EXECUTOR_ID, "TWSE")}
    from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
    assert not build_production_runtime_adapter_registry().routes_for_executor(EXECUTOR_ID)
    with pytest.raises(ValueError, match="unsupported_target"):
        run_i2_candidate_offline_batch([{"canonical_target_id":"TPEX:1234","market":"TPEX",
                                         "instrument_family":"company_share","instrument_type":"common_share"}],
                                       source_payload=json.dumps([row()]).encode(), governed_retrieved_at=STAMP,
                                       transport_retrieved_at=TRANSPORT_STAMP)


def test_i2_catalog_routing_and_default_v3_preview_remain_dormant():
    from server.services.unified_mode_a import validate_mode_a_request
    from scripts.m8r_06_02_mode_b1_preview import build_mode_b1_preview_package

    catalog = json.loads((ROOT / "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json").read_text(encoding="utf-8"))
    routing = json.loads((ROOT / "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json").read_text(encoding="utf-8"))
    cap = next(item for item in catalog["data_need_capabilities"] if item["capability_id"] == "index_futures_context")
    route = next(item for item in routing["routes"] if item["capability_id"] == "index_futures_context")
    assert cap["support_status"] == "contract_supported" and cap["runtime_executable"] is False
    assert route["routing_status"] == "plan_only" and route["selected_executor_id"] is None
    assert route["batching_scope"] == "same_source"
    class FakeSecurityMaster:
        pointer = {"index_path":"fixture/index.json","manifest_path":"fixture/manifest.json","compact_index_sha256":"a"*64,"compact_manifest_sha256":"b"*64}

    request = {"schema_version":"unified_market_evidence_request.v3","request_id":"i2-plan-only",
               "execution_mode":"preview","targets":[{"input":"2330","market_hint":"TWSE"}],
               "data_needs":[{"type":"index_futures_context","priority":"optional","parameters":{}}]}
    validated = validate_mode_a_request(request, allow_fixture_snapshot=True)
    preview = build_mode_b1_preview_package(request, validated, FakeSecurityMaster(), planning_timestamp=STAMP)
    assert preview["validation"]["validation_status"] == "valid"
    assert preview["authorization_created"] is False and preview["network_executed"] is False
    operation = preview["orchestration_plan"]["operations"][0]
    assert operation["operation_status"] == "plan_only_not_executable"
    assert operation["executor_id"] is None and operation["network_required"] is False
    tpex = {**request,"request_id":"i2-tpex-blocked","targets":[{"input":"6488","market_hint":"TPEX"}]}
    tpex_preview = build_mode_b1_preview_package(tpex, validate_mode_a_request(tpex, allow_fixture_snapshot=True), FakeSecurityMaster(), planning_timestamp=STAMP)
    assert tpex_preview["authorization_created"] is False and tpex_preview["network_executed"] is False
    assert all(op.get("executor_id") != EXECUTOR_ID for op in tpex_preview["orchestration_plan"]["operations"])


def test_result_and_audit_v3_accept_additive_i2_phase_i_reference_only():
    result_schema = json.loads((ROOT / "schemas/unified_market_evidence_result.v3.schema.json").read_text(encoding="utf-8"))
    audit_schema = json.loads((ROOT / "schemas/unified_market_evidence_audit_package.v3.schema.json").read_text(encoding="utf-8"))
    projected = evidence([row()]) | {"target": {"canonical_target_id": "TWSE:2330", "market": "TWSE"}}
    jsonschema.Draft7Validator(result_schema, format_checker=jsonschema.FormatChecker())
    definition = result_schema["definitions"]["index_futures_context"]
    result_validator = jsonschema.Draft7Validator(definition, format_checker=jsonschema.FormatChecker())
    result_validator.validate(projected)
    invalid_complete = copy.deepcopy(projected)
    invalid_complete.pop("market_data")
    assert not result_validator.is_valid(invalid_complete)
    invalid_partial = copy.deepcopy(projected)
    invalid_partial["status"] = "partial"
    invalid_partial.pop("market_data")
    invalid_partial["missing_fields"] = ["open"]
    assert not result_validator.is_valid(invalid_partial)
    phase_i_item = audit_schema["properties"]["phase_i_evidence"]["properties"]["evidence_artifact_references"]["items"]
    assert jsonschema.Draft7Validator(phase_i_item).is_valid({"capability_id":"index_futures_context",
        "schema_version":"index_futures_context_evidence.v1","relative_path":"evidence/phase_i/i2/x.json","sha256":"a"*64})


def test_i2_artifact_projects_through_05c_result_v3_and_audit_v3():
    operation_id = "umeop-op-v1-" + "1" * 20
    request_id = "umereq-v2-" + "2" * 20
    target_id = "TWSE:2330"
    request_v2 = _execution_request(target_id, operation_id, request_id)
    payload = json.dumps([row()], separators=(",", ":")).encode()
    candidate = run_i2_candidate_offline_batch([{
        "canonical_target_id": target_id, "market": "TWSE", "instrument_family": "company_share",
        "instrument_type": "common_share", "operation_id": operation_id,
        "execution_request_id": request_id, "execution_request_hash": request_v2["execution_request_hash"],
        "execution_request": request_v2,
    }], source_payload=payload, governed_retrieved_at=STAMP, transport_retrieved_at=TRANSPORT_STAMP,
        fmtqik_benchmark_date="2026-09-29")
    relative_path, body = next(iter(candidate["artifact_bytes"].items()))
    artifact = json.loads(body)
    inventory_item = candidate["artifact_inventory"][0]
    identity = {"canonical_target_id":target_id,"isin":None,"market":"TWSE","security_code":"2330",
                "security_name_zh":"fixture","security_name_en":None,"instrument_family":"company_share","instrument_type":"common_share"}
    req = {"schema_version":"unified_market_evidence_request.v3","request_id":"i2-projection-fixture",
           "execution_mode":"execute","targets":[{"input":"2330","market_hint":"TWSE"}],
           "data_needs":[{"type":"index_futures_context","priority":"required","parameters":{}}]}
    f3 = {"target_results":[{"target_index":0,"original_input":"2330","resolution_status":"resolved","canonical_identity":identity}]}
    plan = {"plan_id":"umeop-v1-"+"3"*20,"plan_hash":"a"*64,"schema_version":"unified_market_evidence_orchestration_plan.v1",
            "plan_status":"plan_ready","input_bindings":{"f3_validation_output_hash":"b"*64},"operations":[
                {"operation_id":operation_id,"capability_id":"index_futures_context","canonical_target_ids":[target_id],"market":"TWSE",
                 "executor_id":EXECUTOR_ID,"operation_status":"executable_pending_approval","expected_evidence_contract":"index_futures_context_evidence.v1","parameters":{}}]}
    bundle = {"bundle_id":"umeb-v1-"+"4"*20,"bundle_hash":"d"*64,"schema_version":"unified_market_evidence_bundle.v1",
              "finalized_at":STAMP,"artifact_inventory":[inventory_item],"operation_evidence_entries":[
                  {"operation_id":operation_id,"status":"succeeded","artifacts":[inventory_item]}]}
    receipt = {"execution_receipt_id":"umerec-v1-"+"5"*20,"execution_receipt_hash":"e"*64,
               "schema_version":"unified_market_evidence_execution_receipt.v1","overall_status":"succeeded","finalized_at":STAMP}
    inputs = ProjectionInputs(
        request=req, f3_validation=f3, plan=plan,
        authorization={"authorization_id":"umea-v1-"+"6"*20,"authorization_hash":"f"*64,"schema_version":"unified_market_evidence_execution_authorization.v1"},
        consumption_binding={"consumption_binding_id":"umeacb-v1-"+"7"*20,"consumption_binding_hash":"1"*64},
        claim={"claim_id":"umecl-v1-"+"8"*20,"consumption_binding_id":"umeacb-v1-"+"7"*20,"consumption_binding_hash":"1"*64,
               "authorization_id":"umea-v1-"+"6"*20,"plan_id":plan["plan_id"],"operator_confirmation_reference":"fixture",
               "state":"consumed_success","finalized_at":STAMP}, receipt=receipt, bundle=bundle,
        artifact_root=".", calculated_at=STAMP, evidence_artifacts={relative_path:artifact},
    )
    lineage = build_lineage_map(inputs)
    assert lineage.bindings[target_id]["index_futures_context"].status == "succeeded"
    citations = build_citation_index(lineage, bundle, "unified_market_evidence_result.v3")
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    result_schema = json.loads((ROOT / "schemas/unified_market_evidence_result.v3.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft7Validator(result_schema, format_checker=jsonschema.FormatChecker()).validate(result)
    typed = result["targets"][0]["evidence"]["index_futures_context"]
    assert typed["target"]["canonical_target_id"] == target_id
    assert set(typed["citation_ids"]).issubset(citations.all_citations)
    audit = build_audit_package(result, inputs, citations, "ai_context/result.v3.json", output_schema_version="unified_market_evidence_audit_package.v3")
    audit_schema = json.loads((ROOT / "schemas/unified_market_evidence_audit_package.v3.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft7Validator(audit_schema, format_checker=jsonschema.FormatChecker()).validate(audit)
    assert audit["phase_i_evidence"]["evidence_artifact_references"] == [{
        "capability_id":"index_futures_context","schema_version":"index_futures_context_evidence.v1",
        "relative_path":relative_path,"sha256":inventory_item["sha256"]}]
    assert audit["phase_h_governance"]["evidence_artifact_references"] == []
