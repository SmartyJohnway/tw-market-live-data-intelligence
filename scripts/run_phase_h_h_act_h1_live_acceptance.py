"""Owner-authorized H-ACT-H1 bounded-live acceptance for TPEx attention.

This is deliberately NOT part of default CI. It performs exactly one fixed
official TPEx OpenAPI request for one exact approved target and persists only
target-bounded governed evidence plus a compact acceptance report.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from jsonschema import Draft202012Validator

import scripts.m8r_06_03_production_adapter as production
from scripts.m8r_05b_03.dispatch import DispatchRuntimeContext


ROOT = Path(__file__).resolve().parents[1]
RESULT_SCHEMA = json.loads(
    (ROOT / "schemas/unified_market_evidence_operation_result.v2.schema.json").read_text(encoding="utf-8")
)
TARGET = "TPEX:6488"
OWNER_AUTHORIZATION_REFERENCE = "OWNER_CHAT_2026-09-22_H_ACT_H1_TPEX_ATTENTION"


def _request() -> dict[str, Any]:
    return {
        "schema_version": "unified_market_evidence_execution_request.v1",
        "execution_request_id": "umereq-v1-" + "1" * 20,
        "execution_request_hash": "1" * 64,
        "operation_id": "umeop-op-v1-" + "2" * 20,
        "batch_group_id": "umeop-batch-v1-" + "3" * 20,
        "plan_id": "h-act-h1-bounded-live-plan",
        "plan_hash": "4" * 64,
        "authorization_id": "umea-v1-" + "5" * 20,
        "authorization_hash": "5" * 64,
        "consumption_binding_id": "umeacb-v1-" + "6" * 20,
        "consumption_binding_hash": "6" * 64,
        "market": "TPEX",
        "approved_security_identifiers": [TARGET],
        "approved_security_types": ["equity"],
        "capability_id": "trading_status_context",
        "executor_id": production.PHASE_H_H1_EXECUTOR_ID,
        "requested_fields": [],
        "currentness_requirement": None,
        "maximum_records": 1,
        "timeout_seconds": 15,
        "network_authorized": True,
        "relative_contained_output_path": "operations/umeop-op-v1-" + "2" * 20 + ".execution-request.json",
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(output_dir: Path) -> dict[str, Any]:
    if os.environ.get("H_ACT_H1_OWNER_AUTHORIZED") != "YES":
        raise RuntimeError("owner_authorization_environment_missing")

    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_root = output_dir / "governed"
    evidence_root.mkdir(parents=True, exist_ok=True)

    calls: list[dict[str, Any]] = []
    original_fetch = production._fetch_official_payload

    def counted_fetch(url: str, *, timeout: int) -> bytes:
        if calls:
            raise RuntimeError("bounded_live_call_limit_exceeded")
        calls.append({"url": url, "timeout_seconds": timeout})
        return original_fetch(url, timeout=timeout)

    production._fetch_official_payload = counted_fetch
    try:
        result = production.production_operation_adapter(
            _request(),
            DispatchRuntimeContext(
                governed_output_root=str(evidence_root),
                mode="execute-approved",
            ),
        )
    finally:
        production._fetch_official_payload = original_fetch

    errors = list(Draft202012Validator(RESULT_SCHEMA).iter_errors(result))
    if errors:
        raise RuntimeError("operation_result_schema_invalid")
    if len(calls) != 1:
        raise RuntimeError(f"unexpected_live_call_count:{len(calls)}")
    if calls[0]["url"] != production.PHASE_H_H1_TPEX_ATTENTION_URL:
        raise RuntimeError("unexpected_live_endpoint")

    artifacts = []
    for artifact in result["evidence_artifacts"]:
        path = evidence_root / artifact["relative_path"]
        if not path.is_file():
            raise RuntimeError("live_evidence_artifact_missing")
        digest = _sha256(path)
        if digest != artifact["sha256"]:
            raise RuntimeError("live_evidence_hash_mismatch")
        artifacts.append({
            "relative_path": artifact["relative_path"],
            "sha256": digest,
            "bytes": path.stat().st_size,
            "schema_version": artifact["schema_version"],
            "artifact_role": artifact["artifact_role"],
        })

    primary = next(
        artifact for artifact in result["evidence_artifacts"]
        if artifact["artifact_role"] == "primary_evidence"
    )
    evidence = json.loads((evidence_root / primary["relative_path"]).read_text(encoding="utf-8"))
    if evidence["target"]["canonical_target_id"] != TARGET:
        raise RuntimeError("live_target_binding_mismatch")
    if evidence["source"]["source_id"] != production.PHASE_H_H1_SOURCE_ID:
        raise RuntimeError("live_source_identity_mismatch")
    if evidence["source"]["activation_state"] != "active":
        raise RuntimeError("live_source_activation_state_mismatch")
    if evidence["coverage"]["covered_status_types"] != ["attention"]:
        raise RuntimeError("live_coverage_scope_mismatch")
    if evidence["coverage"]["declared_scope_complete"] is not False:
        raise RuntimeError("live_false_complete_coverage")
    if evidence["status"] != "partial":
        raise RuntimeError("live_h1_selected_slice_must_remain_partial")

    report = {
        "schema_version": "phase_h_h_act_h1_bounded_live_acceptance.v1",
        "status": "PASS" if result["status"] == "succeeded" else "FAIL",
        "requirement_id": "H0H-LIVE-001",
        "route_id": production.PHASE_H_H1_SOURCE_ID,
        "capability_id": "trading_status_context",
        "target": TARGET,
        "owner_authorization_reference": OWNER_AUTHORIZATION_REFERENCE,
        "network": {
            "authorized": True,
            "call_bound": 1,
            "actual_call_count": len(calls),
            "endpoint": calls[0]["url"],
            "timeout_seconds": calls[0]["timeout_seconds"],
            "retry_count": 0,
            "polling": False,
            "scheduler": False,
            "full_market_payload_persisted": False,
            "target_bounded_governed_artifacts_only": True,
        },
        "operation_result": {
            "schema_version": result["schema_version"],
            "status": result["status"],
            "error_code": result["error_code"],
            "result_item_count": result["result_item_count"],
        },
        "evidence": {
            "schema_version": evidence["schema_version"],
            "status": evidence["status"],
            "source_id": evidence["source"]["source_id"],
            "source_contract_id": evidence["source"]["source_contract_id"],
            "activation_state": evidence["source"]["activation_state"],
            "covered_status_types": evidence["coverage"]["covered_status_types"],
            "uncovered_status_types": evidence["coverage"]["uncovered_status_types"],
            "retrieval_succeeded": evidence["coverage"]["retrieval_succeeded"],
            "source_contract_validated": evidence["coverage"]["source_contract_validated"],
            "exact_target_search_succeeded": evidence["coverage"]["exact_target_search_succeeded"],
            "matched_item_count": len(evidence["items"]),
            "observed_at": evidence["observed_at"],
        },
        "artifacts": artifacts,
    }
    report_path = output_dir / "H_ACT_H1_BOUNDED_LIVE_REPORT.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report["report_sha256"] = _sha256(report_path)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm-bounded-live", action="store_true")
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    if not args.confirm_bounded_live:
        raise SystemExit("H-ACT-H1 live acceptance requires --confirm-bounded-live")
    output = Path(args.output_dir) if args.output_dir else Path(tempfile.mkdtemp(prefix="h-act-h1-"))
    report = run(output)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
