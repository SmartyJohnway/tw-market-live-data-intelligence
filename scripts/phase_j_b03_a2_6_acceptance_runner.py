"""Explicit A2.6 live acceptance entry point; never registers or activates a route."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.phase_j_b03_a2_6_integrated import run_integrated_fixture


def run_live_acceptance() -> dict:
    """Perform one bounded integrated acceptance for the fixed TPEX:6488 target."""
    with tempfile.TemporaryDirectory(prefix="tw-market-a26-") as temporary_root:
        execution = run_integrated_fixture(Path(temporary_root) / "package", use_live_transport=True)
        requests = execution["response_log"]
        counts = {
            "GET": sum(item.get("method") == "GET" for item in requests),
            "HEAD": sum(item.get("method") == "HEAD" for item in requests),
            "POST": sum(item.get("method") == "POST" for item in requests),
        }
        if counts != {"GET": 3, "HEAD": 0, "POST": 0} or len(requests) != 3:
            raise RuntimeError("a26_live_request_accounting_invalid")
        primary = next(item for item in execution["outcomes"][0]["evidence_artifacts"]
                       if item["artifact_role"] == "primary_evidence")
        from scripts.m8r_05c.trading_status_composer import validate_trading_status_context_composite
        composite = json.loads((Path(temporary_root) / "package" / primary["relative_path"]).read_text(encoding="utf-8"))
        validate_trading_status_context_composite(composite)
        drift_codes = (
            "source_failed:invalid_top_level_rows", "source_failed:missing_required_field:",
            "source_failed:invalid_required_field_type:", "source_failed:date_contract_drift:",
            "source_failed:invalid_source_snapshot_date_calendar:",
            "binding_failed:ambiguous_exact_target_rows",
        )
        contract_drift = [item for item in requests if any(
            str(item.get("failure_code", "")).startswith(prefix) for prefix in drift_codes
        )]
        # Component ordering is fixed and artifact hashes are read from the exact
        # persisted references embedded by the composite before the temp dir exits.
        component_hashes = {
            component["source_id"]: component["artifact_reference"]["sha256"]
            for component in composite["components"]
        }
        disposition = (
            "J_B03_A2_6_HOLD_SOURCE_CONTRACT_DRIFT" if contract_drift
            else "J_B03_A2_6_REPRESENTATIVE_INTEGRATED_ACCEPTANCE_PASS_ACTIVATION_READY"
            if all(item.get("http_status") == 200 and item.get("outcome") == "succeeded" for item in requests)
            else "J_B03_A2_6_REPRESENTATIVE_INTEGRATED_ACCEPTANCE_PASS_ACTIVATION_DEFERRED"
        )
        return {
            "disposition": disposition,
            "request_counts": counts,
            "requests": requests,
            "candidate_executor_id": "phase_j_j_b03_tpex_trading_status_composite_candidate",
            "acceptance_authority_hash": execution["authority_hash"],
            "target": {"canonical_target_id": "TPEX:6488", "market": "TPEX", "security_code": "6488"},
            "operation_result_status": execution["outcomes"][0]["status"],
            "receipt_schema": execution["receipt"]["schema_version"],
            "bundle_schema": execution["bundle"]["schema_version"],
            "result_schema": execution["result"]["schema_version"],
            "audit_schema": execution["audit"]["schema_version"],
            "handoff_validated": bool(execution["handoff"]),
            "composite": {
                "sha256": next(item["sha256"] for item in execution["outcomes"][0]["evidence_artifacts"]
                                if item["artifact_role"] == "primary_evidence"),
                "status": composite["status"],
                "aggregate_coverage": composite["aggregate_coverage"],
                "canonical_item_count": composite["canonical_item_count"],
                "native_observation_count": composite["native_observation_count"],
                "components": [
                    {"source_id": item["source_id"], "schema_version": item["evidence_schema_version"],
                     "status": item["component_status"], "sha256": component_hashes[item["source_id"]]}
                    for item in composite["components"]
                ],
            },
            "contract_drift": contract_drift,
            "raw_payload_persisted": False,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live-acceptance", action="store_true",
                        help="perform the Owner-authorized fixed three-GET A2.6 acceptance")
    args = parser.parse_args()
    if not args.live_acceptance:
        parser.error("--live-acceptance is required; this script has no implicit network behavior")
    print(json.dumps(run_live_acceptance(), ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
