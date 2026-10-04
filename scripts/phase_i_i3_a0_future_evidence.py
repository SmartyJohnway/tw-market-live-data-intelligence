"""Pure future evidence attribution; no transport, reservation or persistence."""
from __future__ import annotations
from datetime import date
from scripts.run_phase_i_i3_a0_preflight import CORE, TARGETS, decode_payload, unpack, NOT_APPLICABLE
import hashlib
import json

ATTEMPT3_OUTCOME_SHA256 = "01d4dffa06fc7a78ecc2b4a510badfac511b6f6078f3578af80bbe5abed9f7a1"
ATTEMPT3_TWSE_RESPONSE_SHA256 = "b292ec02ee89e3aa951337e0504662fee7ee2d7509628199e6752fa36860453e"


def _flags(complete_body_received, whole_market_payload_observed):
    if type(complete_body_received) is not bool or type(whole_market_payload_observed) is not bool:
        raise ValueError("observation_flags_must_be_boolean")


def reconstruct_attempt3_twse_canonical_summary(attempt3_record: dict) -> dict:
    """Reconstruct the canonical TWSE analyzer shape from immutable A3 evidence.

    This function accepts the loaded historical record and validates all pinned
    provenance and arithmetic before producing the same eight-key shape as
    ``analyze_market``. It neither reads source payloads nor infers values.
    """
    if not isinstance(attempt3_record, dict):
        raise ValueError("attempt3_record_invalid")
    encoded = (json.dumps(attempt3_record, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if hashlib.sha256(encoded).hexdigest() != ATTEMPT3_OUTCOME_SHA256:
        raise ValueError("attempt3_record_anchor_mismatch")
    if attempt3_record.get("final_decision") != "HOLD":
        raise ValueError("attempt3_historical_decision_mismatch")
    telemetry = attempt3_record.get("source_telemetry", {}).get("TWSE", {})
    payload = attempt3_record.get("source_payload_summaries", {}).get("TWSE", {})
    observations = attempt3_record.get("normalized_observations", {})
    arithmetic = attempt3_record.get("whole_dataset_arithmetic", {}).get("TWSE")
    observation = observations.get("TWSE:1101")
    if (telemetry.get("response_sha256") != ATTEMPT3_TWSE_RESPONSE_SHA256
            or attempt3_record.get("target_binding", {}).get("TWSE:1101") != 1
            or payload.get("row_count") != 1341 or payload.get("field_count") != 19
            or not isinstance(observation, dict) or observation.get("market") != "TWSE"
            or observation.get("security_code") != "1101" or observation.get("trade_date") != "2026-09-30"
            or observation.get("unit") != "share" or not isinstance(arithmetic, dict)):
        raise ValueError("attempt3_twse_evidence_incomplete")
    required = {*CORE, "institutional_total_net"}
    if not required.issubset(arithmetic):
        raise ValueError("attempt3_twse_arithmetic_incomplete")
    checks_pass = all(
        isinstance(arithmetic.get(name), dict)
        and arithmetic[name].get("status") == "PASS"
        and arithmetic[name].get("rows_checked") == 1341
        and arithmetic[name].get("rows_passed") == 1341
        and arithmetic[name].get("rows_failed") == 0
        and arithmetic[name].get("missing_field_rows") == 0
        for name in required
    )
    component = arithmetic.get("dealer_component_net")
    components_pass = (isinstance(component, dict) and component.get("status") == "PASS"
                       and component.get("rows_checked") == 1341
                       and component.get("rows_passed") == 1341
                       and component.get("rows_failed") == 0
                       and component.get("missing_field_rows") == 0)
    status = "PASS" if checks_pass and components_pass else "FAIL"
    selected = {
        "security_code": observation["security_code"],
        "trade_date": observation["trade_date"],
        "unit": observation["unit"],
        "common_core": {name: observation[name] for name in (*CORE, "institutional_total_net_shares")},
        "source_native_optional": observation["source_native_optional"],
    }
    return {
        "market": "TWSE", "exact_matches": 1, "row_count": 1341, "field_count": 19,
        "normalized_trade_dates": ["2026-09-30"], "selected_observation": selected,
        "arithmetic": arithmetic, "status": status,
    }


def source_findings_from_analyzer_result(result: dict | None, *, complete_body_received: bool,
                                        whole_market_payload_observed: bool) -> dict:
    """Adapt the exact canonical analyze_market interface, never helper-shaped input.

    Canonical arithmetic failure is FAIL (not HOLD); downstream preserves those
    statistics and marks semantic_status HOLD. Market is an explicit projection
    from the source summary, not a fabricated analyzer observation field.
    """
    _flags(complete_body_received, whole_market_payload_observed)
    if not complete_body_received:
        if result is not None:
            raise ValueError("partial_payload_semantics_forbidden")
        return {"evaluation_status": "NOT_EVALUATED", "target_binding": None,
                "whole_dataset_arithmetic": None, "unit_proof": None,
                "normalized_observation": None, "batching_observation": "NOT_EVALUATED"}
    if result is None:
        raise ValueError("evaluated_result_required")
    keys = {"market", "exact_matches", "row_count", "field_count", "normalized_trade_dates",
            "selected_observation", "arithmetic", "status"}
    if not isinstance(result, dict) or set(result) != keys:
        raise ValueError("invalid_canonical_analyzer_shape")
    market = result["market"]
    if (market not in TARGETS or type(result["exact_matches"]) is not int or result["exact_matches"] != 1
            or any(type(result[k]) is not int or result[k] < 1 for k in ("row_count", "field_count"))):
        raise ValueError("invalid_canonical_analyzer_binding")
    dates = result["normalized_trade_dates"]
    if not isinstance(dates, list) or len(dates) != 1 or not isinstance(dates[0], str):
        raise ValueError("invalid_canonical_analyzer_dates")
    try:
        if date.fromisoformat(dates[0]).isoformat() != dates[0]:
            raise ValueError()
    except ValueError:
        raise ValueError("invalid_canonical_analyzer_dates") from None
    observation = result["selected_observation"]
    if (not isinstance(observation, dict) or set(observation) != {"security_code", "trade_date", "unit", "common_core", "source_native_optional"}
            or observation["unit"] != "share" or observation["security_code"] != TARGETS[market]
            or observation["trade_date"] != dates[0] or not isinstance(observation["source_native_optional"], dict)):
        raise ValueError("invalid_canonical_observation")
    core = observation["common_core"]
    optional = observation["source_native_optional"]
    allowed_optional = ({"foreign_dealer", "dealer_proprietary", "dealer_hedging", "security_name"}
                        if market == "TWSE" else {"foreign_dealer", "foreign_including_dealer", "security_name"})
    if set(optional) - allowed_optional:
        raise ValueError("invalid_canonical_optional_observation")
    for key, value in optional.items():
        if key == "security_name":
            if not isinstance(value, str) or len(value) > 128:
                raise ValueError("invalid_canonical_optional_observation")
        elif (not isinstance(value, dict) or set(value) != {"buy_shares", "sell_shares", "net_shares"}
              or not all(type(v) is int for v in value.values()) or value["buy_shares"] < 0 or value["sell_shares"] < 0):
            raise ValueError("invalid_canonical_optional_observation")
    if not isinstance(core, dict) or set(core) != {*CORE, "institutional_total_net_shares"}:
        raise ValueError("invalid_canonical_common_core")
    for group, values in core.items():
        if group == "institutional_total_net_shares":
            if type(values) is not int:
                raise ValueError("invalid_canonical_common_core")
        elif (not isinstance(values, dict) or set(values) != {"buy_shares", "sell_shares", "net_shares"}
              or not all(type(v) is int for v in values.values()) or values["buy_shares"] < 0 or values["sell_shares"] < 0):
            raise ValueError("invalid_canonical_common_core")
    checks = result["arithmetic"]
    if not isinstance(checks, dict) or set(checks) != {*CORE, "institutional_total_net", "dealer_component_net"}:
        raise ValueError("invalid_canonical_arithmetic")
    for group, check in checks.items():
        if not isinstance(check, dict) or set(check) != {"status", "rows_checked", "rows_passed", "rows_failed", "missing_field_rows", "first_failure_reason"}:
            raise ValueError("invalid_canonical_arithmetic")
        if any(type(check[k]) is not int or check[k] < 0 for k in ("rows_checked", "rows_passed", "rows_failed", "missing_field_rows")):
            raise ValueError("invalid_canonical_arithmetic")
        reason = check["first_failure_reason"]
        if reason is not None and (not isinstance(reason, str) or len(reason) > 256):
            raise ValueError("invalid_canonical_arithmetic")
        if check["rows_checked"] != check["rows_passed"] + check["rows_failed"] or check["missing_field_rows"] > check["rows_failed"]:
            raise ValueError("invalid_canonical_arithmetic")
        expected = "FAIL" if check["rows_failed"] else "PASS"
        if group == "dealer_component_net" and check["rows_checked"] == 0:
            expected = NOT_APPLICABLE
        if check["status"] != expected or (group != "dealer_component_net" and check["rows_checked"] != result["row_count"]):
            raise ValueError("invalid_canonical_arithmetic")
    status = "FAIL" if any(c["rows_failed"] for c in checks.values()) else "PASS"
    if result["status"] != status:
        raise ValueError("invalid_canonical_analyzer_status")
    return {"evaluation_status": "EVALUATED", "target_binding": result["exact_matches"],
            "whole_dataset_arithmetic": result["arithmetic"],
            "unit_proof": observation["unit"], "normalized_observation": {"market": market, **observation},
            "semantic_status": "PASS" if status == "PASS" else "HOLD",
            "batching_observation": "PROVEN" if whole_market_payload_observed else "NOT_PROVEN"}


def source_findings(result: dict | None, *, complete_body_received: bool,
                    whole_market_payload_observed: bool = False) -> dict:
    """Compatibility name; canonical analyzer input only, observation never inferred."""
    return source_findings_from_analyzer_result(result, complete_body_received=complete_body_received,
        whole_market_payload_observed=whole_market_payload_observed)


def binding_findings_from_payload(market: str, payload, *, complete_body_received: bool,
                                  whole_market_payload_observed: bool) -> dict:
    """Pure pre-analysis binding count. Zero/duplicate are evaluated, not absent.

    Uses the reviewed exact code fields and canonical unpack/decode functions;
    no name matching, analyzer mutation, or normalized observation on failure.
    """
    _flags(complete_body_received, whole_market_payload_observed)
    if not complete_body_received:
        return source_findings_from_analyzer_result(payload, complete_body_received=False,
            whole_market_payload_observed=whole_market_payload_observed)
    if market not in TARGETS:
        raise ValueError("unsupported_market")
    fields, rows = unpack(market, decode_payload(payload))
    code_field = {"TWSE": "證券代號", "TPEX": "SecuritiesCompanyCode"}[market]
    if code_field not in fields:
        raise ValueError("required_code_field_absent")
    count = sum(row.get(code_field) == TARGETS[market] for row in rows)
    return {"evaluation_status": "EVALUATED_BINDING_FAILED" if count != 1 else "EVALUATED_BINDING_ONLY",
            "target_binding": count, "whole_dataset_arithmetic": None, "unit_proof": None,
            "normalized_observation": None,
            "batching_observation": "PROVEN" if whole_market_payload_observed else "NOT_PROVEN"}


def compose_analyzer_evidence(twse_result: dict, tpex_result: dict, dealer_adjudication: dict, *,
                              whole_market_observations: dict, prior_evidence_refs: list[str]) -> dict:
    """Pure Attempt-3-style TWSE + future TPEx canonical source composition."""
    if (dealer_adjudication.get("selection_status") != "RESOLVED"
            or dealer_adjudication.get("selected_candidate") not in {"Dealers-TotalSell", "Dealers -TotalSell"}):
        raise ValueError("dealer_adjudication_not_resolved")
    if twse_result.get("market") != "TWSE" or tpex_result.get("market") != "TPEX":
        raise ValueError("composite_source_market_mismatch")
    statistics = dealer_adjudication.get("candidate_statistics", {})
    if set(statistics) != {"Dealers-TotalSell", "Dealers -TotalSell"}:
        raise ValueError("dealer_adjudication_proof_missing")
    qualifying = [key for key, value in statistics.items() if
                  value.get("rows_checked") == value.get("rows_passed") == tpex_result["row_count"] > 0
                  and value.get("rows_failed") == value.get("missing_rows") == 0]
    independent = dealer_adjudication.get("institutional_total_invariant", {})
    if (qualifying != [dealer_adjudication["selected_candidate"]]
            or independent.get("rows_checked") != tpex_result["row_count"]
            or independent.get("rows_passed") != tpex_result["row_count"]
            or independent.get("rows_failed") != 0 or independent.get("missing_rows") != 0):
        raise ValueError("dealer_adjudication_proof_invalid")
    if set(whole_market_observations) != {"TWSE", "TPEx"}:
        raise ValueError("composite_observation_flags_required")
    sources = {market: source_findings_from_analyzer_result(result, complete_body_received=True,
               whole_market_payload_observed=whole_market_observations[market])
               for market, result in (("TWSE", twse_result), ("TPEx", tpex_result))}
    return {"sources": sources, "dealer_sell_adjudication": dealer_adjudication,
            "semantic_status": "PASS" if all(s["semantic_status"] == "PASS" for s in sources.values()) else "HOLD",
            **batching_findings(sources, prior_evidence_refs), "market_network_calls": 0,
            "raw_payload_persistence": "NONE"}


def batching_findings(sources: dict, prior_evidence_refs: list[str]) -> dict:
    observed = {market: value["batching_observation"] for market, value in sources.items()}
    return {"batching_observation": observed,
            "mixed_market_observation": "PROVEN" if set(observed) == {"TWSE", "TPEx"}
            and all(value == "PROVEN" for value in observed.values()) else "NOT_EVALUATED",
            "batching_contract_support": {"prior_evidence_refs": list(prior_evidence_refs)}}
