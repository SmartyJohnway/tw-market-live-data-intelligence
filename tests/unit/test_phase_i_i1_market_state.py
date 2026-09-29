from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import pytest

from scripts.m8r_05a_f3.request_intake import _catalog_valid
from scripts.m8r_05c.audit_package_builder import build_audit_package
from scripts.m8r_05c.citation_builder import _build_citation_id, build_citation_index
from scripts.m8r_05c.lineage_resolver import build_lineage_map
from scripts.m8r_05c.models import ProjectionInputs
from scripts.m8r_05c.result_builder import build_result
from scripts.validate_phase_i_i1_contracts import I1ValidationError, _json, _pairs, validate_phase_i_i1_contracts
from server.services.phase_i_market_state_adapters import (
    MarketStateNormalizationError,
    assemble_market_state_context,
    normalize_tpex_market_state,
    normalize_twse_market_state,
)
from server.services.unified_mode_b2 import build_mode_b2_authorization
from server.services.unified_mode_a import validate_mode_a_request
from scripts.m8r_06_02_mode_b1_preview import build_mode_b1_preview_package

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests/fixtures/phase_i_i1"
NOW = "2026-09-29T06:00:00Z"


class FakeSecurityMaster:
    pointer = {
        "index_path": "data/security_master/runtime_identity_indexes/sealed/index.json",
        "manifest_path": "data/security_master/runtime_identity_indexes/sealed/manifest.json",
        "compact_index_sha256": "a" * 64,
        "compact_manifest_sha256": "b" * 64,
    }


def _fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_twse_exact_stock_breadth_selected_and_units_preserved():
    result = normalize_twse_market_state(_fixture("twse_fmtqik.json"), _fixture("twse_breadth.json"), retrieved_at=NOW)
    assert result["schema_version"] == "market_state_context_evidence.v1"
    assert result["status"] == "complete"
    assert result["trade_date"] == "2026-09-24"
    assert result["breadth"]["up"] == 601
    assert result["components"]["breadth"]["observed_fields"]["up"] != 999
    assert result["turnover"]["volume_unit"] == "share"
    assert result["turnover"]["value_unit"] == "TWD"
    assert result["source_unit_metadata"]["I1-TWSE-FMTQIK-OPENAPI"]["turnover.value"] == "TWD"
    assert result["benchmark"]["change_points"] == -123.45
    assert result["benchmark"]["change_unit"] == "index_point"
    assert result["currentness_status"] == "unknown"


def test_twse_missing_stock_row_never_falls_back_and_mismatch_preserves_dates():
    overall_only = [{**_fixture("twse_breadth.json")[0]}]
    overall_only[0]["類型"] = "整體市場"
    missing = normalize_twse_market_state(_fixture("twse_fmtqik.json"), overall_only, retrieved_at=NOW)
    assert missing["status"] == "partial"
    assert missing["breadth"] == {}
    assert missing["components"]["breadth"]["status"] == "missing"
    assert any("no 整體市場 fallback" in item for item in missing["caveats"])

    stock = copy.deepcopy(_fixture("twse_breadth.json")[1])
    stock["\u51fa\u8868\u65e5\u671f"] = "1150923"
    mismatch = normalize_twse_market_state(_fixture("twse_fmtqik.json"), [stock], retrieved_at=NOW)
    assert mismatch["status"] == "partial"
    assert mismatch["components"]["fmtqik"]["official_date"] == "2026-09-24"
    assert mismatch["components"]["breadth"]["official_date"] == "2026-09-23"
    assert any("dates preserved" in item for item in mismatch["caveats"])


@pytest.mark.parametrize("mutate,match", [
    (lambda row: row.update({"TradeVolume":"not-a-number"}), "invalid_numeric"),
    (lambda row: row.update({"Date":"bad"}), "invalid_date"),
])
def test_twse_malformed_required_values_fail_closed(mutate, match):
    fmt = _fixture("twse_fmtqik.json")
    mutate(fmt[0])
    with pytest.raises(MarketStateNormalizationError, match=match):
        normalize_twse_market_state(fmt, _fixture("twse_breadth.json"), retrieved_at=NOW)


def test_tpex_units_are_not_scaled_and_exact_source_date_is_normalized():
    result = normalize_tpex_market_state(_fixture("tpex_highlight.json"), retrieved_at=NOW)
    assert result["status"] == "complete"
    assert result["trade_date"] == "2026-09-24"
    assert result["turnover"] == {"value":12345.67,"value_unit":"TWD_million","volume":456789.12,"volume_unit":"thousand_share"}
    assert result["source_unit_metadata"]["I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI"]["turnover.volume"] == "thousand_share"
    assert result["benchmark"]["change_unit"] == "index_point"
    assert result["breadth"]["unmatched_including_suspended"] == 15


@pytest.mark.parametrize("mutate,match", [
    (lambda row: row.pop("CloseIndex"), "missing_required_field"),
    (lambda row: row.update({"Date":"11502330"}), "invalid_date"),
    (lambda row: row.update({"DailyTradingValue":"oops"}), "invalid_numeric"),
])
def test_tpex_missing_or_malformed_required_values_fail_closed(mutate, match):
    rows = _fixture("tpex_highlight.json")
    mutate(rows[0])
    with pytest.raises(MarketStateNormalizationError, match=match):
        normalize_tpex_market_state(rows, retrieved_at=NOW)


def test_assembler_selects_only_frozen_market_rows_and_rejects_unsupported_market():
    twse = assemble_market_state_context(
        "TWSE",
        retrieved_at=NOW,
        twse_fmtqik_rows=_fixture("twse_fmtqik.json"),
        twse_breadth_rows=_fixture("twse_breadth.json"),
    )
    assert twse["status"] == "complete"
    tpex = assemble_market_state_context(
        "TPEX", retrieved_at=NOW,
        tpex_highlight_rows=_fixture("tpex_highlight.json"),
    )
    assert tpex["status"] == "complete"
    with pytest.raises(MarketStateNormalizationError, match="unsupported_market"):
        assemble_market_state_context("TAIFEX", retrieved_at=NOW)


def test_i1_schema_catalog_routing_and_request_are_dormant_and_v3_only():
    validate_phase_i_i1_contracts()
    catalog = _json("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    assert _catalog_valid(catalog)
    cap = next(x for x in catalog["data_need_capabilities"] if x["capability_id"] == "market_state_context")
    assert (cap["support_status"], cap["runtime_executable"], cap["phase_i_activation_state"]) == ("contract_supported", False, "implementation_candidate_inactive")
    assert not {"index_futures_context", "taifex_market_state", "institutional_positioning", "institutional_positioning_context", "market_positioning_context"} & {x["capability_id"] for x in catalog["data_need_capabilities"]}
    for version in ("v1", "v2"):
        schema = _json(f"schemas/unified_market_evidence_request.{version}.schema.json")
        enum = schema["properties"]["data_needs"]["items"]["properties"]["type"]["enum"]
        assert "market_state_context" not in enum
    schema_v3 = _json("schemas/unified_market_evidence_request.v3.schema.json")
    assert "market_state_context" in schema_v3["properties"]["data_needs"]["items"]["properties"]["type"]["enum"]
    request_validator = jsonschema.Draft7Validator(schema_v3)
    valid_i1_request = {
        "schema_version": "unified_market_evidence_request.v3",
        "request_id": "i1-empty-parameters",
        "execution_mode": "preview",
        "targets": [{"input": "2330", "market_hint": "TWSE"}],
        "data_needs": [{"type": "market_state_context", "priority": "required", "parameters": {}}],
    }
    assert request_validator.is_valid(valid_i1_request)
    invalid_i1_request = copy.deepcopy(valid_i1_request)
    invalid_i1_request["data_needs"][0]["parameters"] = {"unexpected": True}
    assert not request_validator.is_valid(invalid_i1_request)
    evidence = normalize_tpex_market_state(_fixture("tpex_highlight.json"), retrieved_at=NOW)
    schema = _json("schemas/market_state_context_evidence.v1.schema.json")
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(evidence)
    twse_evidence = normalize_twse_market_state(
        _fixture("twse_fmtqik.json"), _fixture("twse_breadth.json"), retrieved_at=NOW
    )
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(twse_evidence)
    partial_twse = normalize_twse_market_state(
        _fixture("twse_fmtqik.json"), [], retrieved_at=NOW
    )
    assert partial_twse["status"] == "partial"
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(partial_twse)
    with pytest.raises(I1ValidationError, match="duplicate_json_key"):
        json.loads('{"root":{"field":1,"field":2}}', object_pairs_hook=_pairs)


def test_i1_failure_evidence_is_representable_without_market_values_and_complete_stays_strict():
    evidence_schema = _json("schemas/market_state_context_evidence.v1.schema.json")
    result_schema = _json("schemas/unified_market_evidence_result.v3.schema.json")
    evidence_validator = jsonschema.Draft202012Validator(evidence_schema, format_checker=jsonschema.FormatChecker())
    typed_result_validator = jsonschema.Draft7Validator(result_schema["definitions"]["market_state_context"], format_checker=jsonschema.FormatChecker())
    common = {
        "schema_version": "market_state_context_evidence.v1",
        "market": "TWSE",
        "currentness_status": "unknown",
        "retrieved_at": NOW,
        "components": {"fmtqik": {
            "status": "source_failed",
            "official_date": None,
            "source": {
                "source_id": "I1-TWSE-FMTQIK-OPENAPI",
                "source_family": "TWSE_FMTQIK_OFFICIAL_OPENAPI",
                "source_contract_id": "TWSE_FMTQIK_V1",
                "url": "https://example.invalid/fixture",
                "authority": "official",
                "retrieved_at": NOW,
            },
            "observed_fields": {},
            "unit_metadata": {},
        }},
        "citation_ids": [],
        "caveats": ["No market observation was available in this deterministic fixture."],
    }
    for status in ("unavailable", "source_failed", "binding_failed"):
        item = {**common, "status": status}
        evidence_validator.validate(item)
        typed_result_validator.validate({**item, "target": {"canonical_target_id": "TWSE:2330", "market": "TWSE"}})
        assert "trade_date" not in item
    invalid_complete = {**common, "status": "complete"}
    assert not evidence_validator.is_valid(invalid_complete)
    assert not typed_result_validator.is_valid({**invalid_complete, "target": {"canonical_target_id": "TWSE:2330", "market": "TWSE"}})


def test_i1_partial_can_omit_unavailable_breadth_without_fabrication():
    schema = _json("schemas/market_state_context_evidence.v1.schema.json")
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    partial = normalize_twse_market_state(_fixture("twse_fmtqik.json"), [], retrieved_at=NOW)
    partial.pop("breadth", None)
    partial.pop("breadth_unit", None)
    validator.validate(partial)
    assert partial["status"] == "partial"
    assert "breadth" not in partial


def test_market_state_context_v3_preview_is_plan_only_without_authorization_or_network():
    req = {
        "schema_version":"unified_market_evidence_request.v3",
        "request_id":"i1-dormant-preview",
        "execution_mode":"preview",
        "targets":[{"input":"2330","market_hint":"TWSE"}],
        "data_needs":[{"type":"market_state_context","priority":"required","parameters":{}}],
    }
    result = build_mode_b1_preview_package(req, validate_mode_a_request(req, allow_fixture_snapshot=True), FakeSecurityMaster(), planning_timestamp=NOW)
    assert result["validation"]["validation_status"] == "valid"
    assert result["validation"]["capability_results"][0]["status"] == "contract_supported"
    assert result["preview"]["status"] != "ready_for_confirmation"
    assert result["authorization_created"] is False
    assert result["network_executed"] is False
    operation = result["orchestration_plan"]["operations"][0]
    assert operation["operation_status"] == "plan_only_not_executable"
    assert operation["executor_id"] is None
    assert operation["network_required"] is False
    assert result["orchestration_plan"]["batch_groups"] == []


def test_i1_fixture_artifact_projects_through_lineage_result_v3_and_audit_v3():
    artifact = normalize_tpex_market_state(_fixture("tpex_highlight.json"), retrieved_at=NOW)
    relative_path = "evidence/phase_i/i1/TPEX_market_state.json"
    operation_id = "umeop-op-v1-0123456789abcdef0123"
    artifact["citation_ids"] = [_build_citation_id(operation_id, relative_path)]
    target_id = "TPEX:6488"
    request = {"schema_version":"unified_market_evidence_request.v3","request_id":"i1-projection-fixture","execution_mode":"execute","targets":[{"input":"6488","market_hint":"TPEX"}],"data_needs":[{"type":"market_state_context","priority":"required","parameters":{}}]}
    identity = {"canonical_target_id":target_id,"isin":None,"market":"TPEX","security_code":"6488","security_name_zh":"fixture","security_name_en":None,"instrument_family":"company_share","instrument_type":"common_share"}
    f3 = {"target_results":[{"target_index":0,"original_input":"6488","resolution_status":"resolved","canonical_identity":identity}]}
    plan = {"plan_id":"umeop-v1-0123456789abcdef0123","plan_hash":"a"*64,"schema_version":"unified_market_evidence_orchestration_plan.v1","plan_status":"plan_ready","input_bindings":{"f3_validation_output_hash":"b"*64},"operations":[{"operation_id":operation_id,"capability_id":"market_state_context","canonical_target_ids":[target_id],"market":"TPEX","executor_id":"fixture-only-i1-normalizer","operation_status":"executable_pending_approval","expected_evidence_contract":"market_state_context_evidence.v1","parameters":{}}]}
    inventory = [{"relative_path":relative_path,"sha256":"c"*64,"byte_size":123,"schema_version":"market_state_context_evidence.v1","evidence_contract":"market_state_context_evidence.v1","item_count":1}]
    bundle = {"bundle_id":"umeb-v1-0123456789abcdef0123","bundle_hash":"d"*64,"schema_version":"unified_market_evidence_bundle.v1","finalized_at":NOW,"artifact_inventory":inventory,"operation_evidence_entries":[{"operation_id":operation_id,"status":"succeeded","artifacts":[inventory[0]]}]}
    receipt = {"execution_receipt_id":"umerec-v1-0123456789abcdef0123","execution_receipt_hash":"e"*64,"schema_version":"unified_market_evidence_execution_receipt.v1","overall_status":"succeeded","finalized_at":NOW}
    evidence_path = relative_path
    inputs = ProjectionInputs(
        request=request,
        f3_validation=f3,
        plan=plan,
        authorization={"authorization_id":"umea-v1-0123456789abcdef0123","authorization_hash":"f"*64,"schema_version":"unified_market_evidence_execution_authorization.v1"},
        consumption_binding={"consumption_binding_id":"umecb-v1-0123456789abcdef0123","consumption_binding_hash":"1"*64},
        claim={"claim_id":"umecl-v1-0123456789abcdef0123","consumption_binding_id":"umecb-v1-0123456789abcdef0123","consumption_binding_hash":"1"*64,"authorization_id":"umea-v1-0123456789abcdef0123","plan_id":plan["plan_id"],"operator_confirmation_reference":"fixture","state":"consumed_success","finalized_at":NOW},
        receipt=receipt,
        bundle=bundle,
        artifact_root=".",
        calculated_at=NOW,
        evidence_artifacts={evidence_path:artifact},
    )
    lineage = build_lineage_map(inputs)
    binding = lineage.bindings[target_id]["market_state_context"]
    assert binding.status == "succeeded"
    assert binding.evidence_artifacts[0]["relative_path"] == relative_path
    citations = build_citation_index(lineage, bundle, "unified_market_evidence_result.v3")
    expected_citation = _build_citation_id(operation_id, relative_path)
    assert citations.target_need_citations[f"{target_id}::market_state_context"] == [expected_citation]
    result = build_result(inputs, output_schema_version="unified_market_evidence_result.v3")
    result_schema = _json("schemas/unified_market_evidence_result.v3.schema.json")
    jsonschema.Draft7Validator(result_schema, format_checker=jsonschema.FormatChecker()).validate(result)
    typed = result["targets"][0]["evidence"]["market_state_context"]
    assert typed["schema_version"] == "market_state_context_evidence.v1"
    assert typed["citation_ids"] == [expected_citation]
    assert typed["target"]["canonical_target_id"] == target_id
    assert set(typed["citation_ids"]).issubset(set(citations.all_citations))
    audit = build_audit_package(result, inputs, citations, "ai_context/unified_market_evidence_result.v3.json", output_schema_version="unified_market_evidence_audit_package.v3")
    audit_schema = _json("schemas/unified_market_evidence_audit_package.v3.schema.json")
    jsonschema.Draft7Validator(audit_schema, format_checker=jsonschema.FormatChecker()).validate(audit)
    assert audit["phase_i_evidence"]["evidence_artifact_references"] == [{"capability_id":"market_state_context","schema_version":"market_state_context_evidence.v1","relative_path":relative_path,"sha256":"c"*64}]
    phase_h_enum = audit_schema["properties"]["phase_h_governance"]["properties"]["evidence_artifact_references"]["items"]["properties"]["capability_id"]["enum"]
    assert "market_state_context" not in phase_h_enum
    for phase_h_capability in ("trading_status_context", "corporate_action_context", "recent_performance", "discontinuity_safety"):
        assert phase_h_capability in phase_h_enum
        valid_phase_h_audit = copy.deepcopy(audit)
        valid_phase_h_audit["phase_h_governance"]["evidence_artifact_references"].append({
            "capability_id":phase_h_capability,
            "schema_version":f"{phase_h_capability}_evidence.v1",
            "relative_path":f"evidence/phase_h/{phase_h_capability}.json",
            "sha256":"f"*64,
        })
        jsonschema.Draft7Validator(audit_schema, format_checker=jsonschema.FormatChecker()).validate(valid_phase_h_audit)
    assert not audit["phase_h_governance"]["evidence_artifact_references"] or all(
        ref["capability_id"] != "market_state_context"
        for ref in audit["phase_h_governance"]["evidence_artifact_references"]
    )
    invalid_phase_h_audit = copy.deepcopy(audit)
    invalid_phase_h_audit["phase_h_governance"]["evidence_artifact_references"].append({
        "capability_id":"market_state_context",
        "schema_version":"market_state_context_evidence.v1",
        "relative_path":relative_path,
        "sha256":"c"*64,
    })
    assert not jsonschema.Draft7Validator(audit_schema, format_checker=jsonschema.FormatChecker()).is_valid(invalid_phase_h_audit)
