"""Deterministic receipt generation from explicit execution inputs."""
from __future__ import annotations

from .canonical import receipt_id


def build_receipt(plan: dict, authorization: dict, binding: dict, *, execution_timestamp: str, finished_timestamp: str, operation_results: list[dict], bundle: dict) -> dict:
    rid = receipt_id(authorization_id=authorization["authorization_id"], authorization_hash=authorization["authorization_hash"], plan_hash=plan["plan_hash"], execution_timestamp=execution_timestamp)
    success_count = sum(item["status"] == "success" for item in operation_results)
    return {
        "schema_version": "unified_market_evidence_execution_receipt.v1",
        "receipt_id": rid,
        "plan_id": plan["plan_id"], "plan_hash": plan["plan_hash"],
        "authorization_id": authorization["authorization_id"], "authorization_hash": authorization["authorization_hash"],
        "consumption_binding_id": binding["consumption_binding_id"], "consumption_binding_hash": binding["consumption_binding_hash"],
        "execution_started_at": execution_timestamp, "execution_finished_at": finished_timestamp,
        "approved_operation_ids": list(authorization["approved_operation_ids"]),
        "operation_results": operation_results,
        "successful_operation_count": success_count,
        "failed_operation_count": len(operation_results) - success_count,
        "evidence_bundle_hash": bundle["bundle_hash"],
        "execution_status": bundle["status"],
        "one_shot": True, "scheduler": False, "polling": False, "background_execution": False, "automatic_retry": False,
    }
