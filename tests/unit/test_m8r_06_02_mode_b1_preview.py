import copy
import json
import socket
import urllib.request
from pathlib import Path
from types import SimpleNamespace

import pytest
from scripts.m8r_05b_01.canonical import sha256_json
from scripts.m8r_05b_01.models import PlanningError
from scripts.m8r_06_02_mode_b1_preview import (
    F3_RESOLUTION_TO_SUMMARY,
    build_mode_b1_preview_package,
    build_planning_bindings,
    load_planning_authorities,
    project_canonical_preview,
)
from server.services.unified_mode_a import validate_mode_a_request


ROOT = Path(__file__).resolve().parents[2]
AUTHORITIES = load_planning_authorities()
FIXED_TIME = "2026-08-11T00:00:00Z"


class FakeSecurityMaster:
    pointer = {
        "index_path": "data/security_master/runtime_identity_indexes/sealed/index.json",
        "manifest_path": "data/security_master/runtime_identity_indexes/sealed/manifest.json",
        "compact_index_sha256": "a" * 64,
        "compact_manifest_sha256": "b" * 64,
    }


def request(target="2330", market_hint="TWSE", needs=None, request_id="preview-test"):
    target_value = {"input": target}
    if market_hint is not None:
        target_value["market_hint"] = market_hint
    return {
        "schema_version": "unified_market_evidence_request.v1",
        "request_id": request_id,
        "execution_mode": "preview",
        "targets": [target_value],
        "data_needs": needs
        or [{"type": "current_observation", "priority": "required"}],
    }


def fixture_validation(req):
    return validate_mode_a_request(req, allow_fixture_snapshot=True)


def package(req, validation=None, authorities=None):
    return build_mode_b1_preview_package(
        req,
        validation or fixture_validation(req),
        FakeSecurityMaster(),
        planning_timestamp=FIXED_TIME,
        authorities=authorities or AUTHORITIES,
    )


def test_bindings_cryptographically_bind_request_f3_candidate_and_authorities():
    req = request()
    validation = fixture_validation(req)
    bindings = build_planning_bindings(
        req,
        validation,
        FakeSecurityMaster(),
        capability_catalog=AUTHORITIES["capability_catalog"],
        routing_matrix=AUTHORITIES["routing_matrix"],
        handoff_contract=AUTHORITIES["handoff_contract"],
    )
    assert bindings["original_request_hash"] == sha256_json(req)
    assert bindings["normalized_request_hash"] == sha256_json(
        validation["normalized_request"]
    )
    assert bindings["f3_validation_output_hash"] == sha256_json(validation)
    assert bindings["security_master_evidence_references"] == [
        FakeSecurityMaster.pointer["index_path"],
        FakeSecurityMaster.pointer["manifest_path"],
    ]
    assert bindings["security_master_artifact_hashes"] == ["a" * 64, "b" * 64]


@pytest.mark.parametrize(
    ("target", "market_hint", "expected_status", "summary_field"),
    [
        ("3333", None, "ambiguous_target", "ambiguous"),
        ("NOPE", None, "target_not_plannable", "not_found"),
        ("6488", "TWSE", "target_not_plannable", "market_hint_conflict"),
        ("2881A", "TWSE", "target_not_plannable", "unsupported_security_type"),
    ],
)
def test_real_f3_target_outcomes_map_without_capability_or_error_relabeling(
    target, market_hint, expected_status, summary_field
):
    result = package(request(target, market_hint))
    assert result["preview"]["status"] == expected_status
    assert result["preview"]["target_resolution_summary"][summary_field]
    assert result["preview"]["status"] not in {"unsupported_capability", "error"}


@pytest.mark.parametrize(
    "resolution_status", sorted(F3_RESOLUTION_TO_SUMMARY)
)
def test_every_canonical_f3_resolution_status_has_an_explicit_summary_field(
    resolution_status,
):
    validation = fixture_validation(request())
    target = validation["target_results"][0]
    target["resolution_status"] = resolution_status
    if resolution_status != "resolved":
        target["canonical_identity"] = None
    preview = project_canonical_preview(
        validation,
        None,
        capability_catalog=AUTHORITIES["capability_catalog"],
        routing_matrix=AUTHORITIES["routing_matrix"],
        preview_schema=AUTHORITIES["preview_schema"],
        planning_error="synthetic_projection_only",
    )
    expected_field = F3_RESOLUTION_TO_SUMMARY[resolution_status]
    assert preview["target_resolution_summary"][expected_field]
    if resolution_status == "ambiguous":
        assert preview["status"] == "ambiguous_target"
    elif resolution_status not in {"resolved", "ambiguous"}:
        assert preview["status"] == "target_not_plannable"


def test_real_common_share_preview_is_ready_but_never_authorized_or_executed():
    result = package(request())
    plan = result["orchestration_plan"]
    assert result["preview"]["status"] == "ready_for_confirmation"
    assert plan["plan_status"] == "plan_ready"
    assert plan["operations"][0]["security_types"] == ["equity"]
    assert plan["execution_authorized"] is False
    assert result["network_executed"] is False
    assert result["authorization_created"] is False
    assert result["authorization_consumed"] is False
    assert result["execution_performed"] is False
    assert result["preview"]["caveats"] == [
        "PREVIEW_ONLY",
        "NO_NETWORK_EXECUTED",
        "EXECUTION_NOT_AUTHORIZED",
    ]


@pytest.mark.parametrize(
    ("target", "market", "capability"),
    [
        ("2330", "TWSE", "official_eod_reference"),
        ("6488", "TPEX", "current_observation"),
    ],
)
def test_twse_eod_and_tpex_common_share_use_existing_equity_route(
    target, market, capability
):
    req = request(
        target,
        market,
        [{"type": capability, "priority": "required"}],
    )
    result = package(req)
    assert result["preview"]["status"] == "ready_for_confirmation"
    assert result["orchestration_plan"]["operations"][0]["security_types"] == [
        "equity"
    ]


def test_optional_unimplemented_need_is_partial_and_required_need_is_unsupported():
    optional = request(
        needs=[
            {"type": "current_observation", "priority": "required"},
            {
                "type": "recent_performance",
                "priority": "optional",
                "parameters": {"lookback_trading_days": 5},
            },
        ]
    )
    required = request(
        needs=[
            {
                "type": "recent_performance",
                "priority": "required",
                "parameters": {"lookback_trading_days": 5},
            }
        ]
    )
    assert package(optional)["preview"]["status"] == "partial_possible"
    assert package(required)["preview"]["status"] == "unsupported_capability"


def test_session_required_is_honestly_unsupported_by_current_planner_route():
    req = request(needs=[{"type": "session_status", "priority": "required"}])
    result = package(req)
    assert result["preview"]["status"] == "unsupported_capability"
    assert result["orchestration_plan"]["plan_status"] == "blocked"


def test_target_limit_is_resource_rejection_and_invalid_request_has_no_preview():
    limit_req = request()
    limit_req["targets"] = [{"input": str(index)} for index in range(51)]
    limit_result = package(limit_req)
    assert limit_result["preview"]["status"] == "rejected_resource_bound"

    invalid_req = {"schema_version": "wrong", "request_id": "bad"}
    invalid_result = package(invalid_req, fixture_validation(invalid_req))
    assert invalid_result["validation"]["request_schema_status"] == "invalid"
    assert invalid_result["preview"] is None
    assert invalid_result["orchestration_plan"] is None


def test_actual_f3_duplicate_target_is_non_plannable():
    req = request()
    req["targets"] = [
        {"input": "2330", "market_hint": "TWSE"},
        {"input": "TWSE:2330"},
    ]
    result = package(req)
    assert [target["resolution_status"] for target in result["validation"]["target_results"]] == [
        "resolved",
        "duplicate",
    ]
    assert result["preview"]["status"] == "target_not_plannable"
    assert result["preview"]["target_resolution_summary"]["duplicate"] == [
        "TWSE:2330"
    ]


def test_taifex_provisional_eod_is_honestly_not_executable():
    req = request(
        "TX",
        "TAIFEX",
        [{"type": "official_eod_reference", "priority": "required"}],
    )
    validation = fixture_validation(request())
    validation["normalized_request"] = copy.deepcopy(req)
    validation["target_results"][0]["canonical_identity"].update(
        {
            "canonical_target_id": "TAIFEX:TX",
            "market": "TAIFEX",
            "security_code": "TX",
            "instrument_family": "derivative",
            "instrument_type": "futures",
        }
    )
    validation["target_results"][0]["original_input"] = "TX"
    validation["capability_results"] = [
        {
            "data_need_index": 0,
            "capability_id": "official_eod_reference",
            "priority": "required",
            "status": "provisional",
        }
    ]
    result = package(req, validation)
    assert result["orchestration_plan"]["plan_status"] == "blocked"
    assert result["preview"]["status"] == "unsupported_capability"
    assert result["orchestration_plan"]["execution_authorized"] is False


def test_hard_operation_limit_projects_resource_rejection():
    authorities = copy.deepcopy(AUTHORITIES)
    authorities["capability_catalog"]["bounds"]["hard_operation_limit"] = 0
    req = request()
    validation = fixture_validation(req)
    result = package(req, validation, authorities)
    assert result["preview"]["status"] == "rejected_resource_bound"
    assert result["orchestration_plan"] is None


def test_plan_identity_is_deterministic_across_planning_timestamps():
    req = request()
    validation = fixture_validation(req)
    first = build_mode_b1_preview_package(
        req,
        validation,
        FakeSecurityMaster(),
        planning_timestamp="2026-08-11T00:00:00Z",
        authorities=AUTHORITIES,
    )
    second = build_mode_b1_preview_package(
        req,
        validation,
        FakeSecurityMaster(),
        planning_timestamp="2026-08-12T00:00:00Z",
        authorities=AUTHORITIES,
    )
    assert first["orchestration_plan"]["plan_hash"] == second["orchestration_plan"][
        "plan_hash"
    ]
    assert first["orchestration_plan"]["plan_id"] == second["orchestration_plan"][
        "plan_id"
    ]
    assert first["preview"]["internal_execution_reference"] == second["preview"][
        "internal_execution_reference"
    ]


def test_mode_b1_package_does_not_use_network(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("external network is forbidden in Mode B1 Preview")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(urllib.request, "urlopen", forbidden)
    result = package(request())
    assert result["preview"]["status"] == "ready_for_confirmation"


def test_malformed_planning_authority_fails_closed():
    authorities = copy.deepcopy(AUTHORITIES)
    authorities["preview_schema"] = {"type": "not-a-json-schema-type"}
    with pytest.raises(PlanningError, match="input_schema_invalid: preview_schema"):
        package(request(), authorities=authorities)


def test_invalid_projected_preview_is_an_internal_output_contract_error():
    authorities = copy.deepcopy(AUTHORITIES)
    authorities["preview_schema"] = {"type": "object", "required": ["missing"]}
    with pytest.raises(PlanningError, match="output_schema_invalid: preview"):
        package(request(), authorities=authorities)


def test_fund_product_etf_remains_non_executable_at_preview_boundary():
    validation = fixture_validation(request())
    identity = validation["target_results"][0]["canonical_identity"]
    identity.update(
        {
            "canonical_target_id": "TWSE:0050",
            "security_code": "0050",
            "instrument_family": "fund_product",
            "instrument_type": "etf",
        }
    )
    result = package(request("0050", "TWSE"), validation)
    assert result["preview"]["status"] == "unsupported_capability"
    assert result["orchestration_plan"]["plan_status"] == "blocked"
    assert result["orchestration_plan"]["blocked_operations"][0][
        "blocking_reason_codes"
    ] == ["unsupported_security_type"]


def test_production_service_independently_reruns_f3_for_the_supplied_request(
    monkeypatch,
):
    from server.services import unified_mode_b1

    calls = []

    def validate(req):
        calls.append(copy.deepcopy(req))
        return fixture_validation(req)

    monkeypatch.setattr(unified_mode_b1, "validate_mode_a_request", validate)
    monkeypatch.setattr(
        unified_mode_b1,
        "get_production_mode_a_security_master",
        lambda _path: FakeSecurityMaster(),
    )
    req = request(request_id="service-revalidation")
    result = unified_mode_b1.build_mode_b1_preview(
        req, planning_timestamp=FIXED_TIME
    )
    assert calls == [req]
    assert result["validation"]["request_id"] == "service-revalidation"
    assert result["orchestration_plan"]["execution_authorized"] is False


def test_workbench_exposes_preview_and_mode_b2_controls():
    html = (
        ROOT / "frontend/unified-workbench/UnifiedMarketEvidenceWorkbench.html"
    ).read_text(encoding="utf-8")
    javascript = (
        ROOT / "frontend/unified-workbench/unified-workbench.js"
    ).read_text(encoding="utf-8")
    assert 'id="btn-preview"' in html
    assert "PREVIEW ONLY" in html
    assert "NO NETWORK EXECUTED" in html
    assert "NOT AUTHORIZED" in html
    assert 'id="btn-authorize"' in html
    assert 'id="btn-execute-once"' in html
    assert "/api/unified/preview-request" in javascript
    assert "validatedRequestFingerprint" in javascript
    assert "invalidateDerivedState" in javascript
