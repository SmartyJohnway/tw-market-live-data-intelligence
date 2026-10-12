#!/usr/bin/env python3
"""Validate the R5-P1-R2 TPEx historical coverage qualification network-free."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORD_PATH = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_SM_B1_R5_P1_R2_TPEX_HISTORICAL_COVERAGE_QUALIFICATION_2026-10-10.json"
MANIFEST_PATH = ROOT / "skills/tw-security-master-classifier/references/source-manifest.json"
PARSER_PATH = ROOT / "skills/tw-security-master-classifier/scripts/parse_tpex_delisted.py"
MATERIALIZER_PATH = ROOT / "scripts/m8r_06_01b_materialize_production_inputs.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    record = json.loads(RECORD_PATH.read_text(encoding="utf-8"))
    assert record["gate"] == "J-B04-A6-SM-B1-R5-P1-R2"
    assert record["starting_authority"] == {
        "head": "05583ea56b5bfe79d81a6f1b2686c63ce3fa06ef",
        "tree": "b4c6a94ceb68ec1e5228e730eda16bbca35acd10",
        "main": "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a",
        "tracked_worktree_clean": True,
        "R5_P1_R1_independent_review_id": "5478113925",
        "R5_P1_R1_disposition": "PASS_AS_PARTIAL",
        "endpoint_discovery": "COMPLETE_ENOUGH",
        "coverage_qualification": "INCOMPLETE",
    }
    assert record["owner_authorization"]["statement_sha256"] == "e7b57d5550a897417d79b5cc78d7e4c530ccc834dc65a552c457b33225d4a5e0"
    accounting = record["probe_accounting"]
    assert accounting["logical_probes_used"] == accounting["explicit_http_dispatches_used"] == accounting["endpoint_post_requests_used"] == 4
    assert accounting["GET"] == accounting["HEAD"] == accounting["redirects_followed"] == accounting["automatic_retries"] == 0
    assert accounting["POST"] == 4 and accounting["browser_incidental_requests"] == 0

    coverage = record["coverage"]
    assert coverage["complete_all_result_obtained"] is True
    assert coverage["returned_row_count"] == coverage["totalCount"] == 582
    assert coverage["row_count_reconciled"] is True
    assert coverage["duplicate_security_code_effective_date_identities"] == 0
    assert coverage["invalid_dates"] == 0
    assert coverage["earliest_effective_date"] == "1992-10-27"
    assert coverage["latest_effective_date"] == "2026-10-01"
    assert record["paging_qualification"]["current_tranche_requested_size"] == 1000
    assert record["paging_qualification"]["all_history_single_response"] is True
    assert record["paging_qualification"]["page_2_or_final_page_required_for_qualified_request"] is False
    assert record["bootstrap_fit"]["classification"] == "COMPATIBLE_WITH_EXISTING_BOOTSTRAP_ENVELOPE"
    assert record["bootstrap_fit"]["production_dispatches_for_tpex"] == 1
    assert record["bootstrap_fit"]["bootstrap_executed"] is False
    assert record["bootstrap_fit"]["bootstrap_attempt_2_authorized"] is False

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    source = next(item for item in manifest["lifecycle_sources"] if item["id"] == "tpex_company_delisted")
    contract = source["lifecycle_data_contract"]
    assert source["url"] == "https://www.tpex.org.tw/www/zh-tw/company/deListed"
    assert source["format"] == "json" and source["contract_state"] == "qualified_data_contract"
    assert source["production_automatic_acquisition"] is True
    assert source["landing_page_contract"]["url"] == "https://www.tpex.org.tw/zh-tw/mainboard/listed/delisted.html"
    assert contract["state"] == "qualified" and contract["request"]["method"] == "POST"
    assert contract["request"]["paging_size"] == 1000
    assert contract["request"]["fixed_parameters"]["date"] == "ALL"
    assert contract["request"]["fixed_parameters"]["reason"] == "-1"
    historical_manifest = subprocess.check_output(
        ["git", "show", f"{record['implementation']['commit']}:{MANIFEST_PATH.relative_to(ROOT).as_posix()}"],
        cwd=ROOT,
    )
    assert hashlib.sha256(historical_manifest).hexdigest() == record["implementation"]["production_manifest_sha256"]

    materializer = MATERIALIZER_PATH.read_text(encoding="utf-8")
    assert "BOOTSTRAP_TPEX_LIFECYCLE_DATA_CONTRACT_UNRESOLVED" in materializer
    assert 'request_options = {\n                "method": "POST"' in materializer
    assert "BOOTSTRAP_TPEX_LIFECYCLE_SOURCE_FAILURE" in materializer
    assert "BOOTSTRAP_LIFECYCLE_SCHEMA_DRIFT" in materializer
    parser = PARSER_PATH.read_text(encoding="utf-8")
    for code in (
        "tpex_api_invalid_json", "tpex_api_application_error",
        "tpex_api_incomplete_all_response", "tpex_api_invalid_roc_date",
        "tpex_api_duplicate_lifecycle_identity",
    ):
        assert code in parser
    assert "MAX_ALL_ROWS = 1000" in parser

    for artifact in record["local_evidence"]["raw_responses"]:
        path = Path(artifact["path"])
        if path.exists():
            assert path.stat().st_size == artifact["bytes"]
            assert sha256(path) == artifact["sha256"]
    r1_json = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_SM_B1_R5_P1_R1_TPEX_LIFECYCLE_CONTRACT_QUALIFICATION_2026-10-10.json"
    r1_md = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A6_SM_B1_R5_P1_R1_TPEX_LIFECYCLE_CONTRACT_QUALIFICATION_2026-10-10.md"
    assert sha256(r1_json) == record["historical_evidence"]["R5_P1_R1_json_sha256"]
    assert sha256(r1_md) == record["historical_evidence"]["R5_P1_R1_markdown_sha256"]

    status = subprocess.run(
        [sys.executable, str(ROOT / "scripts/manage_security_master.py"), "status"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    )
    assert json.loads(status.stdout)["status"] == "NOT_INITIALIZED"
    assert not (ROOT / "data/security_master/active.json").exists()
    assert record["canonical_state"]["production_identity_verified"] is False
    assert record["canonical_state"]["H2"] == "INACTIVE"
    assert record["canonical_state"]["routing"] == "plan_only"
    assert record["canonical_state"]["selected_executor"] is None
    assert record["canonical_state"]["J-B04"] == "BLOCKING"
    assert record["canonical_state"]["Phase_J"] == "NOT_STARTED"
    assert record["canonical_state"]["MCP"] == 6
    assert record["network_counts"]["security_master_bootstrap_live_acquisition"] == 0
    print("J-B04-A6-SM-B1-R5-P1-R2 validator PASS (source contract qualified; bootstrap unauthorized)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
