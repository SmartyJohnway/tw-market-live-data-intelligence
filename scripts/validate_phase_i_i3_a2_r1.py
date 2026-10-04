"""Offline, fail-closed validation of the I3-A2 optional-detail repair."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import validate_phase_i_i3_a2_candidate as a2

OWNER = "USER_CHAT_2026-10-03_PHASE_I_I3_A2_R1_OPTIONAL_SOURCE_NATIVE_FAILURE_SEMANTICS_CLOSURE"
RECORD = "docs/governance/phase_i/PHASE_I_I3_A2_R1_OPTIONAL_SOURCE_NATIVE_FAILURE_SEMANTICS_CLOSURE_2026-10-03.json"
START_HEAD = "81a3667a52fe354555cb87705a15ec2301a695b6"
START_TREE = "659e56f20f08ea99cd6f725a8fe755b7917cf5d6"
SCHEMA_SHA = "3be9a0ca3cf0e0bb5badb427231d47ce86fdb604ae28cb31582b0f9612c76f7c"
FIXTURES = ROOT / "tests/fixtures/phase_i_i3_a0"


def require(condition: bool, code: str) -> None:
    if not condition:
        raise ValueError(code)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _target(market: str, code: str) -> dict:
    return {"market": market, "security_code": code, "canonical_target_id": f"{market}:{code}",
            "instrument_family": "company_share", "instrument_type": "common_share",
            "execution_eligibility": "allowed", "operation_id": "r1-validation",
            "execution_request_id": "umereq-v2-" + "1" * 20,
            "execution_request_hash": "1" * 64}


def _evidence(market: str, source: object) -> dict:
    from server.services.phase_i_i3_cash_institutional_flow_offline_candidate import run_i3_candidate_offline_batch
    body = json.dumps(source, ensure_ascii=False).encode("utf-8")
    output = run_i3_candidate_offline_batch([_target(market, "1101" if market == "TWSE" else "5347")],
        source_payloads={market: body}, retrieved_at_by_market={market: "2026-10-03T00:00:00Z"},
        twse_governed_source_date="20260930" if market == "TWSE" else None)
    require(output["network_calls"] == 0 and output["retry_count"] == 0, "candidate_network_accounting")
    return json.loads(next(iter(output["artifact_bytes"].values())))


def validate(*, require_record: bool = True) -> dict | None:
    def deny(*args, **kwargs):
        raise AssertionError("r1_external_network_forbidden")
    with patch("socket.socket.connect", deny), patch("socket.create_connection", deny):
        a2.validate()
        require(sha(ROOT / a2.SCHEMA) == SCHEMA_SHA, "schema_changed")
        require(sha(ROOT / a2.RECORD) == a2.RECORD_SHA256, "original_a2_record_changed")
        twse = json.loads((FIXTURES / "twse_synthetic.json").read_text(encoding="utf-8"))
        tpex = json.loads((FIXTURES / "dealer_sell_adjudication_scenarios.json").read_text(encoding="utf-8"))["unique_candidate_a"]
        twse_name = twse["fields"].index("證券名稱")
        twse["fields"].pop(twse_name)
        for row in twse["data"]:
            row.pop(twse_name)
        good = _evidence("TWSE", twse)
        require(good["status"] == "complete" and "security_name" not in good["source_native_optional"]
                and "optional source-native field unavailable: security_name" in good["caveats"], "twse_optional_name")
        foreign = twse["fields"].index("外資自營商買進股數")
        twse["data"][0][foreign] = "malformed"
        good = _evidence("TWSE", twse)
        require(good["status"] == "complete" and "foreign_dealer" not in good["source_native_optional"]
                and good["institutional_total_net_shares"] == 140, "twse_optional_foreign_dealer")
        proprietary = twse["fields"].index("自營商買賣超股數(自行買賣)")
        twse["data"][0][proprietary] = "malformed"
        failed = _evidence("TWSE", twse)
        require(failed["status"] == "source_failed" and "source_native_optional" not in failed, "twse_required_reconciliation")
        for row in tpex:
            row.pop("CompanyName", None)
        good = _evidence("TPEX", tpex)
        require(good["status"] == "complete" and "security_name" not in good["source_native_optional"], "tpex_optional_name")
        require("foreign_dealer" not in good["source_native_optional"]
                and "foreign_including_dealer" not in good["source_native_optional"], "tpex_optional_groups")
        record = None
        if require_record:
            record = json.loads((ROOT / RECORD).read_text(encoding="utf-8"))
            require(record["schema_version"] == "phase_i_i3_a2_r1_optional_source_native_failure_semantics_closure.v1"
                    and record["status"] == "A2_R1_PASS" and record["owner_authority"] == OWNER,
                    "r1_record_identity")
            require(record["starting_main"] == a2.BASELINE and record["starting_head"] == START_HEAD
                    and record["starting_tree"] == START_TREE, "r1_starting_authority")
            require(record["a1_contract"]["sha256"] == a2.a1.sha(ROOT / a2.a1.CONTRACT)
                    and record["original_a2"]["record_sha256"] == a2.RECORD_SHA256
                    and record["original_a2"]["technical_commit"] == a2.HISTORICAL_TECHNICAL_COMMIT
                    and record["original_a2"]["technical_tree"] == a2.HISTORICAL_TECHNICAL_TREE,
                    "r1_historical_provenance")
            technical = record["technical_repair"]
            require(subprocess.check_output(["git", "rev-parse", technical["commit"] + "^{tree}"], cwd=ROOT).decode().strip() == technical["tree"], "r1_commit_tree")
            for rel in (*a2.MODULES, a2.SCHEMA, "tests/unit/test_phase_i_i3_a2_offline.py", "scripts/validate_phase_i_i3_a2_candidate.py", "scripts/validate_phase_i_i3_a2_r1.py"):
                require((ROOT / rel).read_bytes() == subprocess.check_output(["git", "show", f"{technical['commit']}:{rel}"], cwd=ROOT), f"r1_technical_drift:{rel}")
            require(record["schema_sha_before"] == SCHEMA_SHA and record["schema_sha_after"] == SCHEMA_SHA
                    and record["schema_unchanged"] is True, "r1_schema_provenance")
            repair = record["repair"]
            for key in ("TWSE_security_name_optional", "TPEX_security_name_optional",
                        "TWSE_foreign_dealer_optional", "TPEX_foreign_dealer_optional",
                        "TPEX_foreign_including_dealer_optional",
                        "TWSE_dealer_proprietary_reconciliation_mandatory",
                        "TWSE_dealer_hedging_reconciliation_mandatory",
                        "common_core_whole_dataset_arithmetic_unchanged",
                        "foreign_dealer_excluded_from_institutional_total"):
                require(repair[key] is True, f"r1_repair_claim:{key}")
            require(repair["optional_issue_scope"] == "target_row_only"
                    and repair["optional_failure_behavior"] == "omit_affected_group_with_bounded_caveat_no_zero_fill"
                    and repair["failure_evidence_numeric_observations_fabricated"] is False, "r1_failure_semantics_claim")
            counts = record["validation"]
            require(counts["R1_specific"] == {"passed": 14, "skipped": 0, "deselected": 39}
                    and counts["A2_only"] == {"passed": 53, "skipped": 0, "deselected": 0}
                    and counts["I3_SSL_focused"] == {"passed": 269, "skipped": 0, "deselected": 0}
                    and counts["default_ci"] == {"passed": 1139, "skipped": 1, "deselected": 5}
                    and counts["full_current"] == {"passed": 1512, "skipped": 1, "deselected": 5}, "r1_validation_counts")
            require(record["network_calls"] == 0 and record["raw_payload_persistence"] is False
                    and record["production_authority_changed"] is False
                    and (record["I1_active_sources"], record["I1_production_routes"]) == (3, 2)
                    and (record["I2_active_sources"], record["I2_production_routes"]) == (1, 1)
                    and (record["I3_active_sources"], record["I3_production_routes"]) == (0, 0)
                    and record["A2_independent_review_after_R1"] == "PASS"
                    and record["A3_ready_for_separate_owner_decision"] is True
                    and record["A3_authorized"] is False
                    and record["production_activation_authorized"] is False
                    and record["merge_authorized"] is False, "r1_authorization_boundary")
    print("I3-A2-R1 PASS; optional detail isolated; TWSE reconciliation strict; market GETs=0")
    return record


if __name__ == "__main__":
    validate(require_record="--technical-only" not in sys.argv)
