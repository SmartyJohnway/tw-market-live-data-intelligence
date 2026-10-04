"""Offline, fail-closed validator for the I3-A1 frozen source/evidence contract."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_phase_i_i3_a0_preflight import PROTECTED
from scripts.phase_i_i3_a4_compat import assert_candidate_is_dormant, assert_non_i3_authority_unchanged

PREFIX = "docs/governance/phase_i/"
CONTRACT = PREFIX + "PHASE_I_I3_A1_CASH_INSTITUTIONAL_FLOW_SOURCE_EVIDENCE_CONTRACT_2026-10-03_FROZEN.json"
BASELINE = "dafa5999c63d34d55a4665c6534aa77477448d79"
OWNER = "USER_CHAT_2026-10-03_PHASE_I_I3_A1_CASH_INSTITUTIONAL_FLOW_SOURCE_EVIDENCE_CONTRACT_FREEZE"
EVIDENCE = {
    "attempt3_twse_outcome_sha256": (PREFIX + "PHASE_I_I3_A0_ATTEMPT_3_SOURCE_TIMING_SYMMETRY_REPROBE_2026-10-02.json", "01d4dffa06fc7a78ecc2b4a510badfac511b6f6078f3578af80bbe5abed9f7a1"),
    "attempt3_p3_erratum_sha256": (PREFIX + "PHASE_I_I3_A0_ATTEMPT_3_EVIDENCE_ERRATUM_2026-10-03.json", "9f86216243fb4d9885e58d9dd7bb231373d4d222e6e277f6565533e942d37196"),
    "attempt4_tpex_outcome_sha256": (PREFIX + "PHASE_I_I3_A0_ATTEMPT_4_TPEX_ONLY_SOURCE_CLOSURE_2026-10-03.json", "0e24c5f55716f512051c1db5fb3eaead921693875f66ec00bd15e84d469028c5"),
    "final_composite_sha256": (PREFIX + "PHASE_I_I3_A0_FINAL_COMPOSITE_CLOSURE_2026-10-03.json", "497361ce6c7c6ed628a8a17e8dcf3a9586d4448f15c405739853e2faa5484fd8"),
    "authority_chain_v3_sha256": (PREFIX + "PHASE_I_I3_A0_FUTURE_ATTEMPT_AUTHORITY_CHAIN_V3.json", "14e1f6eebfbffda74883448895ec4a9ddb3ef54a983f39b9da3d6496a738f5d8"),
}
TWSE_RESPONSE = "b292ec02ee89e3aa951337e0504662fee7ee2d7509628199e6752fa36860453e"
TPEX_RESPONSE = "2d058996bf67a375e152f381dda1a8610c32cf3ecd1ed31240c89ac7fd020402"
P0_MAPPING = PREFIX + "PHASE_I_I3_A0_CASH_INSTITUTIONAL_FLOW_PROBE_MAPPING_V1.json"
P0_MAPPING_SHA = "e3af3d8b5ce11fe88f0c32efa45400126fe1991ec0c0725fbc3f480e2888638c"


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def independent_semantic_assertions(contract: dict) -> None:
    """Check source-field and formula semantics without consulting the A0 GO flag."""
    source = contract["sources"]
    require(sha(ROOT / P0_MAPPING) == P0_MAPPING_SHA, "historical_mapping_changed")
    probe = json.loads((ROOT / P0_MAPPING).read_text(encoding="utf-8"))["markets"]
    for market in ("TWSE", "TPEX"):
        actual = source[market]
        expected = probe[market]
        core = json.loads(json.dumps(expected["required_common_core"]))
        if market == "TPEX":
            core["dealer_total"]["sell_shares"] = ["Dealers-TotalSell"]
        require(actual["required_common_core"] == core, f"{market}_common_core_semantics")
        require(actual["source_native_optional"] == expected["source_native_optional"], f"{market}_optional_semantics")
        require(actual["code_field"] == expected["code_field"] and actual["date_field"] == expected["date_field"]
                and actual["date_encoding"] == expected["date_encoding"], f"{market}_identity_date_semantics")
    tpex = source["TPEX"]
    require(tpex["required_common_core"]["foreign_and_mainland_excluding_foreign_dealer"]["sell_shares"] ==
            [" Foreign Investors include Mainland Area Investors (Foreign Dealers excluded)-Total Sell"], "tpex_leading_space_lost")
    require(tpex["rejected_dealer_sell_alias"] == "Dealers -TotalSell"
            and tpex["dealer_sell_live_adjudication"] == {"selected_rows_passed": 910, "selected_rows_failed": 0, "alias_rows_passed": 802, "alias_rows_failed": 108}, "dealer_sell_adjudication")
    semantic = contract["semantic_contract"]
    require(semantic == {
        "participant_semantic_symmetry": "ASSERT_INDEPENDENTLY",
        "foreign_common_group": "foreign_and_mainland_excluding_foreign_dealer",
        "foreign_dealer": "source_native_optional_excluded_from_common_total",
        "foreign_including_dealer": "source_native_optional_not_common_core_substitute",
        "trust_common_group": "investment_trust",
        "dealer_common_group": "dealer_total",
        "institutional_total_formula": ["foreign_and_mainland_excluding_foreign_dealer.net_shares", "investment_trust.net_shares", "dealer_total.net_shares"],
        "net_formula": "buy_shares - sell_shares",
        "whole_dataset_arithmetic_required": True,
        "twse_component_reconciliation_required": True,
        "tpex_component_reconciliation_required": False,
        "invariant_failure_status": "source_failed",
    }, "participant_semantic_symmetry")
    require(source["TWSE"]["dealer_component_split"] == "REQUIRED_RECONCILIATION"
            and tpex["dealer_component_split"] == "NOT_APPLICABLE_SOURCE_DOES_NOT_EXPOSE_COMPONENT_SPLIT", "dealer_component_semantics")


def validate_contract(contract: dict) -> dict:
    require(contract["schema_version"] == "phase_i_i3_a1_cash_institutional_flow_source_evidence_contract.v1"
            and contract["gate"] == "I3-A1" and contract["status"] == "FROZEN_PASS"
            and contract["owner_authority"] == OWNER and contract["capability_id"] == "cash_institutional_flow_context", "a1_identity")
    independent_semantic_assertions(contract)
    target = contract["target"]
    require(target == {"markets": ["TWSE", "TPEX"], "instrument_family": "company_share", "instrument_type": "common_share",
            "execution_eligibility": "allowed", "identity_authority": "installation_local_security_master", "durable_identity": "ISIN",
            "routing_identity": "MARKET:CODE", "binding": "exact_security_code_unique", "name_fallback": False}, "target_identity")
    twse, tpex = contract["sources"]["TWSE"], contract["sources"]["TPEX"]
    require(set(contract["sources"]) == {"TWSE", "TPEX"}, "source_market_scope")
    require(twse["source_id"] == "I3-TWSE-T86-INSTITUTIONAL-TRADING" and twse["authority"] == "official"
            and twse["endpoint_family"] == "https://www.twse.com.tw/rwd/zh/fund/T86"
            and twse["parameters"] == {"date": "explicit_Gregorian_YYYYMMDD", "selectType": "ALLBUT0999", "response": "json"}
            and twse["method"] == "GET" and twse["root_shape"] == "object_fields_data"
            and twse["automatic_previous_trading_day_fallback"] is False
            and twse["hidden_date_substitution"] is False and twse["calendar_today_implies_current"] is False, "twse_source_date_contract")
    require(tpex["source_id"] == "I3-TPEX-3INSTI-DAILY-TRADING" and tpex["authority"] == "official"
            and tpex["endpoint"] == "https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading"
            and tpex["method"] == "GET" and tpex["root_shape"] == "array_of_objects"
            and tpex["gregorian_year_offset"] == 1911 and tpex["one_normalized_source_date_required"] is True
            and tpex["historical_backfill"] is False, "tpex_source_date_contract")
    require(twse["transport"] == {"tls_policy": "compatibility", "certificate_verification": True, "hostname_verification": True,
            "verify_mode": "CERT_REQUIRED", "verify_x509_strict": "clear_only_where_supported", "unsafe_tls": False,
            "silent_policy_fallback": False, "timeout_seconds": 30, "retry_count": 0, "redirect_policy": "reject",
            "maximum_response_bytes": 4194304, "accepted_mime": ["application/json"], "raw_persistence": False}, "twse_transport")
    require(tpex["transport"] == {"tls_policy": "strict", "timeout_seconds": 30, "retry_count": 0,
            "redirect_policy": "reject", "maximum_response_bytes": 4194304, "read_chunk_bytes": 65536,
            "accepted_mime": ["application/json"], "complete_body_required": True, "partial_body_analysis": False,
            "unsafe_tls": False, "raw_persistence": False}, "tpex_transport")
    require(twse["acquisition_grain"] == tpex["acquisition_grain"] == "whole_market", "acquisition_grain")
    require(twse["publication_context"] == {"18:00": "daily_product_excluding_block_trades", "20:00": "daily_product_including_block_trades",
            "publication_phase_in_payload": "absent", "infer_phase_from_retrieved_at": False}
            and tpex["publication_timestamp_in_payload"] == "absent" and tpex["same_day_finality"] == "unknown", "publication_timing")
    ev = contract["normalized_evidence"]
    require(ev["schema_version"] == "cash_institutional_flow_context_evidence.v1" and ev["grain"] == "per_security_trade_date"
            and ev["unit"] == "share" and ev["buy_sell"] == "non_negative_integer_shares"
            and ev["net"] == "signed_integer_shares" and ev["implicit_lot_multiplier"] is False
            and ev["statuses"] == ["complete", "unavailable", "source_failed", "binding_failed"]
            and ev["partial_status"] is False and ev["binding_failed_when"] == "exact_target_match_count_not_one"
            and ev["unavailable_only"] == "explicit_qualified_no_usable_evidence_without_contract_violation"
            and "whole_dataset_invariant_failure" in ev["source_failed_conditions"]
            and "partial_body" in ev["source_failed_conditions"]
            and "participant_semantics_pass" in ev["complete_requires"], "evidence_contract")
    require(set(ev["required_fields"]) == {"schema_version", "status", "market", "security_code", "trade_date", "retrieved_at", "unit",
            "foreign_and_mainland_excluding_foreign_dealer", "investment_trust", "dealer_total", "institutional_total_net_shares",
            "publication_finality", "currentness_status", "source", "transport", "citation_ids", "caveats"}, "evidence_required_fields")
    timing = contract["timing"]
    require(timing == {"source_trade_dates": "independent", "alignment_statuses": ["same_trade_date", "different_trade_date", "not_comparable", "unavailable"],
            "same_date_implies_simultaneous_publication": False, "different_date_numeric_same_session_interpretation": False,
            "date_rewriting": False, "required_fields": ["trade_date", "retrieved_at", "publication_finality", "currentness_status"],
            "publication_finality_enum": ["known_final", "unknown"], "v1_publication_finality_without_separate_authority": "unknown",
            "currentness_without_separate_authority": "unknown", "retrieved_at_alone_proves_finality": False}, "timing_contract")
    require(contract["batching"] == {"TWSE_max_acquisitions": 1, "TPEX_max_acquisitions": 1, "mixed_max_unique_acquisitions": 2,
            "per_target_refetch": False, "retry_count": 0, "provenance": {"TWSE": "Attempt_3", "TPEX": "Attempt_4"}}, "batching_contract")
    require(contract["raw_payload_persistence"] == "FORBIDDEN" and contract["interpretation"] == "descriptive_observations_only"
            and set(contract["excluded_product_semantics"]) == {"trading_signal", "bullish_bearish", "sentiment", "smart_money",
            "causal_interpretation", "investment_recommendation", "security_ranking", "flow_score_or_percentile",
            "rolling_accumulation_5d_20d", "historical_backfill_or_warehouse", "day_trading", "margin_short_lending",
            "TAIFEX_positioning", "options_PCR", "large_trader_positioning", "ETF_exact_holdings"}, "product_boundary")
    require(contract["authorization_boundary"] == {"a1_contract_frozen": True, "a1_market_gets": {"TWSE": 0, "TPEX": 0, "TAIFEX": 0, "other": 0},
            "a2_ready_for_separate_owner_decision": True, "a2_implementation_authorized": False, "production_runtime_implementation": False,
            "source_activation": False, "route_activation": False, "merge_authorized": False}, "authorization_boundary")
    return contract


def validate() -> dict:
    def deny(*args, **kwargs):
        raise AssertionError("a1_external_network_forbidden")
    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        contract = json.loads((ROOT / CONTRACT).read_text(encoding="utf-8"))
        validate_contract(contract)
        for key, (rel, expected) in EVIDENCE.items():
            require(sha(ROOT / rel) == expected and contract["a0_evidence"][key] == expected, f"a0_anchor_{key}")
        require(contract["a0_evidence"]["decision"] == "GO_PASS", "a0_decision_pin")
        attempt3 = json.loads((ROOT / EVIDENCE["attempt3_twse_outcome_sha256"][0]).read_text(encoding="utf-8"))
        attempt4 = json.loads((ROOT / EVIDENCE["attempt4_tpex_outcome_sha256"][0]).read_text(encoding="utf-8"))
        composite = json.loads((ROOT / EVIDENCE["final_composite_sha256"][0]).read_text(encoding="utf-8"))
        require(attempt3["source_telemetry"]["TWSE"]["response_sha256"] == TWSE_RESPONSE
                and attempt4["tpex_transport"]["response_sha256"] == TPEX_RESPONSE
                and contract["a0_evidence"]["twse_response_sha256"] == TWSE_RESPONSE
                and contract["a0_evidence"]["tpex_response_sha256"] == TPEX_RESPONSE, "a0_response_hashes")
        adjudication = composite["dealer_sell_adjudication"]
        require(composite["final_A0_decision"] == "GO_PASS" and composite["participant_semantic_symmetry"] == "PASS"
                and adjudication["selected_candidate"] == "Dealers-TotalSell"
                and adjudication["candidate_statistics"]["Dealers-TotalSell"]["rows_passed"] == 910
                and adjudication["candidate_statistics"]["Dealers -TotalSell"]["rows_failed"] == 108, "a0_semantic_provenance")
        for rel in PROTECTED:
            if rel.endswith(".json") and rel in {PROTECTED[0], PROTECTED[1], PROTECTED[6], PROTECTED[7], PROTECTED[8]}:
                assert_non_i3_authority_unchanged(rel)
            else:
                require((ROOT / rel).read_bytes() == subprocess.check_output(["git", "show", f"{BASELINE}:{rel}"], cwd=ROOT), f"production_drift:{rel}")
        from scripts.m8r_06_03_production_adapter import build_production_runtime_adapter_registry
        from server.unified_mcp.tool_contracts import build_tool_specs
        registry = build_production_runtime_adapter_registry()
        require(len(registry.routes_for_executor("phase_i_i1_market_state_executor")) == 2
                and len(registry.routes_for_executor("phase_i_i2_index_futures_context_executor")) == 1, "production_routes")
        require(json.loads((ROOT / "docs/data_capabilities/phase_i_i1_source_authority.v1.json").read_text(encoding="utf-8"))["active_source_count"] == 3
                and json.loads((ROOT / "docs/data_capabilities/phase_i_i2_source_authority.v1.json").read_text(encoding="utf-8"))["active_source_count"] == 1, "production_sources")
        catalog = json.loads((ROOT / PROTECTED[0]).read_text(encoding="utf-8"))
        assert_candidate_is_dormant(PROTECTED[0], PROTECTED[1])
        require(len(build_tool_specs()) == 6, "mcp_six_tools")
    print("I3-A1 FROZEN_PASS; A0 anchors intact; semantic assertions independent; production unchanged; market GETs=0")
    return contract


if __name__ == "__main__":
    validate()
