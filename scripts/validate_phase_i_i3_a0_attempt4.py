"""Offline integrity validator for the consumed, TPEx-only A0 Attempt 4."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import phase_i_i3_a0_attempt_authority as authority
from scripts.phase_i_i3_a0_future_evidence import reconstruct_attempt3_twse_canonical_summary, source_findings_from_analyzer_result

P = "docs/governance/phase_i/"
OUTCOME = P + "PHASE_I_I3_A0_ATTEMPT_4_TPEX_ONLY_SOURCE_CLOSURE_2026-10-03.json"
COMPOSITE = P + "PHASE_I_I3_A0_FINAL_COMPOSITE_CLOSURE_2026-10-03.json"
RESERVATION = P + "acceptance_runs/i3-a0-attempt4-authority-reservation.json"
CONSUMED = P + "acceptance_runs/i3-a0-attempt4-authority-consumed.json"
OWNER = "USER_CHAT_2026-10-03_PHASE_I_I3_A0_FRESH_ATTEMPT_4_TPEX_ONLY_FINAL_COMPOSITE_CLOSURE_AUTHORIZATION"
BASELINE = "dafa5999c63d34d55a4665c6534aa77477448d79"
START = "8be2cfe795b10591be564b441a17094df2884d1e"
TREE = "24c188f0949008761470fe5d48af74c62fe83b7e"
ATTEMPT3_SHA = "01d4dffa06fc7a78ecc2b4a510badfac511b6f6078f3578af80bbe5abed9f7a1"
P3_SHA = "9f86216243fb4d9885e58d9dd7bb231373d4d222e6e277f6565533e942d37196"
V3_SHA = "14e1f6eebfbffda74883448895ec4a9ddb3ef54a983f39b9da3d6496a738f5d8"
PLAN_SHA = "68a36d26137e91068b881d21559d4981465ae39691545aac222a533b483082bf"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> dict:
    outcome_path, composite_path = ROOT / OUTCOME, ROOT / COMPOSITE
    reservation_path, consumed_path = ROOT / RESERVATION, ROOT / CONSUMED
    for path in (outcome_path, composite_path, reservation_path, consumed_path):
        if not path.is_file():
            raise ValueError(f"required_attempt4_artifact_missing:{path.name}")
    outcome, composite = (json.loads(p.read_text(encoding="utf-8")) for p in (outcome_path, composite_path))
    reservation, consumed = (json.loads(p.read_text(encoding="utf-8")) for p in (reservation_path, consumed_path))
    chain = authority.load_reviewed_authority_chain(version="v3", attempt_number=4)
    plan_path = ROOT / P / "PHASE_I_I3_A0_ATTEMPT_4_READINESS_PLAN_V2_2026-10-03.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if (sha(authority.AUTHORITY_V3_PATH) != V3_SHA or sha(plan_path) != PLAN_SHA
            or plan.get("status") != "NON_EXECUTABLE_CONFIGURATION_ONLY"
            or plan.get("authority_chain_version") != "v3" or plan.get("attempt_4_ready") is not True
            or plan.get("attempt_4_authorized") is not False
            or plan.get("markets") != {"TWSE": {"max_gets": 0}, "TPEx": {"max_gets": 1, "ssl_policy": "strict"}}
            or plan.get("retry") != 0 or plan.get("redirect_policy") != "reject"):
        raise ValueError("attempt4_readiness_authority_invalid")
    authority.validate_reservation(reservation, chain)
    authority.validate_consumed_latch(consumed, chain)
    if (outcome.get("owner_authority") != OWNER or outcome.get("baseline_main") != BASELINE
            or outcome.get("starting_branch_head") != START or outcome.get("starting_tree") != TREE):
        raise ValueError("attempt4_owner_or_starting_authority_mismatch")
    if (outcome.get("authority_v3", {}).get("sha256") != V3_SHA
            or outcome.get("readiness_plan_v2", {}).get("sha256") != PLAN_SHA):
        raise ValueError("attempt4_reviewed_authority_mismatch")
    if reservation.get("owner_authority") != OWNER or consumed.get("owner_authority") != OWNER:
        raise ValueError("attempt4_latch_owner_mismatch")
    if (not consumed.get("consumed") or consumed.get("consumed_before_first_http_attempt") is not True
            or reservation.get("reserved") is not True or reservation.get("consumed") is not False):
        raise ValueError("attempt4_latch_state_invalid")
    if outcome.get("reservation", {}).get("sha256") != sha(reservation_path) or outcome.get("consumed_latch", {}).get("sha256") != sha(consumed_path):
        raise ValueError("attempt4_latch_digest_mismatch")
    if outcome.get("attempt4_decision") not in {"GO_PASS", "HOLD", "NO_GO"}:
        raise ValueError("attempt4_decision_invalid")
    if outcome.get("actual_get_counts") != {"TWSE": 0, "TPEx": 1, "TAIFEX": 0, "other_market_data": 0}:
        raise ValueError("attempt4_network_budget_exceeded")
    if outcome.get("network_budget") != {"TWSE_max_get": 0, "TPEx_max_get": 1, "total_max_get": 1, "retry_count": 0}:
        raise ValueError("attempt4_network_budget_invalid")
    transport = outcome["tpex_transport"]
    if (transport.get("ssl_policy") != "strict" or transport.get("retry_count") != 0
            or transport.get("redirect_policy") != "reject" or transport.get("timeout_seconds") != 30):
        raise ValueError("attempt4_transport_policy_invalid")
    if transport.get("endpoint") != "https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading" or transport.get("method") != "GET":
        raise ValueError("attempt4_source_endpoint_invalid")
    if outcome.get("raw_payload_persistence") != "NONE" or outcome.get("raw_body_written") is not False:
        raise ValueError("attempt4_raw_persistence_invalid")
    if any(outcome.get(k) is not False for k in ("A1_authorized", "implementation_authorized", "production_activation_authorized", "merge_authorized")):
        raise ValueError("attempt4_authority_boundary_invalid")
    twse = outcome["pre_network_twse_reconstruction"]
    summary = twse["canonical_summary"]
    findings = twse["adapter_validation"]
    if (twse.get("source_record_sha256") != ATTEMPT3_SHA or twse.get("source_response_sha256") != "b292ec02ee89e3aa951337e0504662fee7ee2d7509628199e6752fa36860453e"
            or twse.get("status") != "PASS" or summary["status"] != "PASS"
            or findings["evaluation_status"] != "EVALUATED" or findings["target_binding"] != 1
            or findings["semantic_status"] != "PASS" or findings["unit_proof"] != "share"):
        raise ValueError("attempt4_twse_reconstruction_invalid")
    tpex = outcome["canonical_tpex_analyzer_result"]
    projection = outcome["tpex_future_evidence_projection"]
    if outcome["attempt4_decision"] == "GO_PASS":
        if (not transport.get("complete_body_received") or transport.get("error_code") is not None
                or transport.get("http_status") != 200 or transport.get("base_mime") != "application/json"
                or type(transport.get("response_byte_count")) is not int or transport["response_byte_count"] > 4 * 1024 * 1024
                or not re.fullmatch(r"[0-9a-f]{64}", transport.get("response_sha256", ""))):
            raise ValueError("attempt4_go_transport_proof_invalid")
        if (outcome.get("target_binding") != 1 or outcome.get("target_binding_status") != "EVALUATED_BINDING_ONLY"
                or outcome.get("source_semantics_state") != "EVALUATED" or not isinstance(tpex, dict)
                or tpex.get("market") != "TPEX" or tpex.get("exact_matches") != 1 or tpex.get("status") != "PASS"
                or tpex.get("row_count") != outcome["tpex_payload_summary"].get("row_count")
                or tpex.get("field_count") != outcome["tpex_payload_summary"].get("field_count")):
            raise ValueError("attempt4_go_tpex_analysis_invalid")
        if (outcome["dealer_sell_adjudication"].get("selection_status") != "RESOLVED"
                or outcome["dealer_sell_adjudication"].get("selected_candidate") not in {"Dealers-TotalSell", "Dealers -TotalSell"}
                or outcome["dealer_sell_adjudication"]["institutional_total_invariant"].get("rows_failed") != 0):
            raise ValueError("attempt4_go_dealer_adjudication_invalid")
        if projection.get("evaluation_status") != "EVALUATED" or projection.get("unit_proof") != "share" or projection.get("semantic_status") != "PASS" or projection.get("batching_observation") != "PROVEN":
            raise ValueError("attempt4_go_projection_invalid")
        if (composite.get("final_A0_decision") != "GO_PASS" or composite.get("attempt4_tpex_source_sha256") != sha(outcome_path)
                or composite.get("attempt3_twse_source_sha256") != ATTEMPT3_SHA
                or composite.get("attempt3_p3_erratum_sha256") != P3_SHA or composite.get("authority_v3_sha256") != V3_SHA
                or composite.get("batching", {}).get("mixed_market_observation") != "PROVEN"):
            raise ValueError("attempt4_go_composite_invalid")
        if composite.get("trade_date_symmetry", {}).get("classification") != "different_trade_date":
            raise ValueError("attempt4_trade_date_attribution_invalid")
    elif composite.get("final_A0_decision") != outcome["attempt4_decision"]:
        raise ValueError("attempt4_hold_composite_mismatch")
    if sha(ROOT / ATTEMPT3_REL) != ATTEMPT3_SHA or sha(ROOT / P3_ERRATUM_REL) != P3_SHA:
        raise ValueError("historical_attempt3_evidence_changed")
    print(f"Attempt 4 integrity PASS; decision={outcome['attempt4_decision']}; market calls=1; retry=0; network=validator-offline")
    return outcome


ATTEMPT3_REL = P + "PHASE_I_I3_A0_ATTEMPT_3_SOURCE_TIMING_SYMMETRY_REPROBE_2026-10-02.json"
P3_ERRATUM_REL = P + "PHASE_I_I3_A0_ATTEMPT_3_EVIDENCE_ERRATUM_2026-10-03.json"


if __name__ == "__main__":
    validate()
