"""Aggregate only contained, contract-matched operation evidence."""
from __future__ import annotations

from .canonical import sha256_json


def aggregate(plan: dict, authorization: dict, operation_results: list[dict]) -> dict:
    successes = [item for item in operation_results if item["status"] == "success"]
    failures = [item for item in operation_results if item["status"] != "success"]
    bundle = {
        "schema_version": "unified_market_evidence_bundle.v1",
        "plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"],
        "authorization_id": authorization["authorization_id"], "authorization_hash": authorization["authorization_hash"],
        "scope_hash": authorization["scope_hash"],
        "evidence": [{"operation_id": item["operation_id"], "evidence_contract": item["expected_evidence_contract"], "evidence": item["evidence"]} for item in successes],
        "omissions": [{"operation_id": item["operation_id"], "reason_code": item["omission_reason"]} for item in failures],
        "status": "complete" if not failures else ("partial" if successes else "failed"),
        "raw_payload_retained": False,
    }
    bundle["bundle_hash"] = sha256_json(bundle)
    return bundle
