#!/usr/bin/env python3
"""Validate the network-free R5-P2-R1 ETN contract promotion and evidence."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_SM_B1_R5_P2_R1_TWSE_ETN_EVIDENCE_COVERAGE_QUALIFICATION_2026-10-10.json"
R5_P2_JSON = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_SM_B1_R5_P2_TWSE_LIFECYCLE_REDIRECT_CONTRACT_QUALIFICATION_2026-10-10.json"
R5_P2_MD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_SM_B1_R5_P2_TWSE_LIFECYCLE_REDIRECT_CONTRACT_QUALIFICATION_2026-10-10.md"
BASE = "d411933247487075e250f41db87688fe02fa5740"
LANDING_SHA = "265d3eeb30e292795ad9a089f6e34f10c6c5b781b756c9766f796717b97cb8d9"
DATA_SHA = "e049ed302b3bdd7b73bc77a3c8d2d015835da6882db8652f397d4c8514019484"
ETN_URL = "https://www.twse.com.tw/rwd/zh/ETN/expireEnd?response=json"


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate_json_key:{key}")
        result[key] = value
    return result


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)


def git_blob(revision: str, path: str) -> bytes:
    return subprocess.check_output(["git", "show", f"{revision}:{path}"], cwd=ROOT)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    record = load(RECORD)
    r5_p2 = load(R5_P2_JSON)
    assert record["gate"] == "J-B04-A6-SM-B1-R5-P2-R1"
    assert record["disposition"] == "SM_B1_R5_P2_R1_TWSE_ETN_CONTRACT_QUALIFIED_BOOTSTRAP_FIT"
    assert record["authorized_starting_authority"] == {
        "head": BASE,
        "tree": "acb77b24a32677279fff7a16869231899fb25747",
        "main": "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a",
        "tracked_worktree_clean": True,
    }
    assert record["prior_r5_p2_review"]["review_id"] == "5478481588"
    assert r5_p2["overall_disposition"] == "SM_B1_R5_P2_TWSE_LIFECYCLE_CONTRACTS_PARTIAL"
    assert r5_p2["sources"]["twse_etn_expired"]["disposition"] == "SOURCE_CONTRACT_PARTIAL"
    assert record["owner_authorization"]["statement_sha256"] == "5467ebfa813bae9ddea8a4b1e501c5c70d5423b30b206f6d7e1a7b6d137bd32d"

    evidence = record["evidence_storage"]["artifacts"]
    by_path = {item["path"]: item for item in evidence}
    for path, digest in (("/tmp/j-b04-a6-sm-b1-r5-p2-r1/raw/001-etn-landing.html", LANDING_SHA),
                         ("/tmp/j-b04-a6-sm-b1-r5-p2-r1/raw/002-etn-data-default.json", DATA_SHA)):
        item = by_path[path]
        assert item["sha256"] == digest
        local = Path(path)
        assert local.exists() and local.stat().st_size == item["bytes"] and sha(local.read_bytes()) == digest
    assert record["probes"][0]["matches_r5_p2_landing_hash"] is True
    assert record["probes"][0]["matches_r5_p2_historical_byte_count"] is True
    assert record["evidence_storage"]["raw_write_once"] is True
    assert record["evidence_storage"]["unique_raw_paths"] is True

    ledger = Path(record["evidence_storage"]["ledger_path"])
    rows = [json.loads(line, object_pairs_hook=reject_duplicates) for line in ledger.read_text().splitlines()]
    assert len(rows) == 2
    assert [row["method"] for row in rows] == ["GET", "GET"]
    assert all(row["source_id"] == "twse_etn_expired" and row["dispatch_reservations"] == 1 for row in rows)
    assert rows[0]["sha256"] == LANDING_SHA and rows[1]["sha256"] == DATA_SHA

    landing = record["landing_page_contract"]
    assert landing["form_count"] == 1 and landing["data_api"] == "/ETN/expireEnd"
    assert landing["form_controls"] == [] and landing["hidden_defaults"] == []
    assert landing["onload_arguments"] == {} and landing["date_year_status_code_reason_type_filters"] == []
    assert landing["data_paging"] is False and landing["data_server_side"] is False
    assert landing["initial_request_count"] == 1 and landing["initial_request_method"] == "GET"
    request = record["request_contract"]
    assert request["canonical_url"] == ETN_URL and request["method"] == "GET"
    assert request["query_parameters"] == {"response": "json"}
    assert request["explicit_endpoint_call_count"] == 1 and request["paging_parameters"] == []
    response = record["response_contract"]
    assert response["root_keys_exact"] == ["stat", "title", "data", "fields"]
    assert response["success_stat"] == "ok" and response["observed_row_count"] == 13
    assert len(response["fields_exact_order"]) == 5
    coverage = record["coverage"]
    assert coverage["complete_dataset_offered_by_landing_report_proven"] is True
    assert coverage["source_data_is_unfiltered"] is True and coverage["source_data_is_unpaged"] is True
    assert coverage["limitation"].startswith("Complete only for the dataset offered")
    fit = record["bootstrap_fit"]
    assert fit["classification"] == "COMPATIBLE_WITH_EXISTING_BOOTSTRAP_ENVELOPE"
    assert fit["logical_source_probes"] == 5 and fit["twse_etn_dispatches"] == 1
    assert fit["global_hard_ceiling"] == 10 and fit["envelope_changed"] is False

    manifest_path = "skills/tw-security-master-classifier/references/source-manifest.json"
    current_manifest = load(ROOT / manifest_path)
    base_manifest = json.loads(git_blob(BASE, manifest_path), object_pairs_hook=reject_duplicates)
    current_etn = next(item for item in current_manifest["lifecycle_sources"] if item["id"] == "twse_etn_expired")
    base_etn = next(item for item in base_manifest["lifecycle_sources"] if item["id"] == "twse_etn_expired")
    assert current_etn["url"] == ETN_URL and current_etn["format"] == "json"
    assert current_etn["contract_state"] == "qualified_data_contract"
    assert current_etn["production_automatic_acquisition"] is True
    assert current_etn["events"] == ["twse_delisted"]
    assert base_etn["url"] == "https://www.twse.com.tw/zh/products/securities/etn/products/expire.html"
    assert [item for item in current_manifest["lifecycle_sources"] if item["id"] != "twse_etn_expired"] == [item for item in base_manifest["lifecycle_sources"] if item["id"] != "twse_etn_expired"]

    materializer = (ROOT / "scripts/m8r_06_01b_materialize_production_inputs.py").read_text(encoding="utf-8")
    assert f'TWSE_ETN_EXPIRED_URL = "{ETN_URL}"' in materializer
    assert 'BOOTSTRAP_TWSE_ETN_LIFECYCLE_SOURCE_FAILURE = "BOOTSTRAP_TWSE_ETN_LIFECYCLE_SOURCE_FAILURE"' in materializer
    assert 'if is_twse_etn_api:' in materializer
    assert '"BLOCKED_BY_TWSE_ETN_LIFECYCLE_SOURCE_FAILURE"' in materializer
    assert 'parser_name == "parse_twse_etn_expired_json"' in materializer
    assert "data-paging" in current_etn["landing_page_contract"]["paging"]
    parser = (ROOT / "skills/tw-security-master-classifier/scripts/parse_etn_termination.py").read_text(encoding="utf-8")
    for code in ("twse_etn_json_malformed_json", "twse_etn_json_non_ok_stat", "twse_etn_json_fields_drift",
                 "twse_etn_json_row_width_drift", "twse_etn_json_invalid_date", "twse_etn_json_duplicate_lifecycle_identity"):
        assert code in parser
    tests = (ROOT / "tests/unit/test_m8r_06_01b_bootstrap_dispatch_budget.py").read_text(encoding="utf-8")
    assert "test_twse_etn_transport_failure_stops_before_phase_e_and_export" in tests
    assert "test_twse_etn_schema_drift_is_distinct_and_blocks_phase_e_export" in tests
    assert "test_twse_etn_wrong_content_type_is_schema_drift_before_parser" in tests

    implementation = record["implementation"]
    assert implementation["commit"] == "eba68f0c0f37c56c1aad6e60da1f0f557f414773"
    assert implementation["tree"] == "c3629c3ecf5b26829b7f7e7bc7f3c914b889ea1f"
    assert record["validation"]["focused_pytest"] == {"collected": 101, "passed": 101, "failed": 0, "skipped": 0}
    ci = record["validation"]["default_ci"]
    assert ci["base_counts"] == ci["candidate_counts"]
    assert ci["new_failure_delta"] == 0 and ci["candidate_failure_set_expanded"] is False
    assert record["source_network_counts"] == {"GET": 2, "HEAD": 0, "POST": 0, "Security_Master_live_acquisition": 0}
    assert record["historical_state_preserved"]["r5_p2_json_rewritten"] is False
    assert record["historical_state_preserved"]["r5_p2_markdown_rewritten"] is False
    assert sha(git_blob(BASE, R5_P2_JSON.relative_to(ROOT).as_posix())) == sha(R5_P2_JSON.read_bytes())
    assert sha(git_blob(BASE, R5_P2_MD.relative_to(ROOT).as_posix())) == sha(R5_P2_MD.read_bytes())
    assert record["security_master"]["state"] == "NOT_INITIALIZED"
    assert record["security_master"]["production_identity_verified"] is False
    assert record["security_master"]["active_json_present"] is False
    assert record["security_master"]["bootstrap_attempt_2"] == "NOT_AUTHORIZED"
    assert record["canonical_runtime_state"] == {
        "H2": "INACTIVE", "routing": "plan_only", "selected_executor": None,
        "J-B04": "BLOCKING", "Phase_J": "NOT_STARTED", "MCP": 6,
    }
    if (ROOT / "data/security_master/active.json").exists():
        raise AssertionError("unexpected_active_security_master")
    print("R5-P2-R1 ETN qualification validator PASS (no bootstrap; historical R5-P2 preserved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
