"""Commit 3 evidence aggregation: collect adapter dispatch outcomes and compute overall status."""
from __future__ import annotations

from typing import Any

from .dispatch import request_identity
from .errors import OrchestrationError


def aggregate_dispatch_outcomes(
    preflight: dict[str, Any],
    dispatch_outcomes: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(dispatch_outcomes, list) or not dispatch_outcomes:
        raise OrchestrationError("dispatch_outcomes_empty")

    approved_order = preflight["approved_operation_order"]
    total_ops = len(approved_order)
    if len(dispatch_outcomes) != total_ops:
        raise OrchestrationError("dispatch_outcomes_count_mismatch")

    requests = preflight.get("bounded_execution_requests", [])
    requests_by_op = {r.get("operation_id"): r for r in requests if isinstance(r, dict)}
    bindings = preflight.get("resolved_operation_bindings", {})

    seen_ops = set()
    succeeded = 0
    failed = 0
    total_items = 0
    op_receipts = []
    bundle_entries = []
    artifact_inventory = []
    aggregate_warnings: list[str] = []

    for idx, outcome in enumerate(dispatch_outcomes):
        op_id = outcome.get("operation_id")
        if not op_id or op_id not in requests_by_op:
            raise OrchestrationError("unknown_operation_id")
        if op_id in seen_ops:
            raise OrchestrationError("duplicate_operation_id")
        if op_id != approved_order[idx]:
            raise OrchestrationError("aggregation_order_mismatch")
        seen_ops.add(op_id)

        req = requests_by_op[op_id]
        binding = bindings.get(op_id, {})
        expected_req_id, expected_req_hash = request_identity(req)

        if (
            outcome["execution_request_id"] != expected_req_id
            or outcome["execution_request_hash"] != expected_req_hash
        ):
            raise OrchestrationError("request_identity_mismatch")

        if (
            outcome["executor_id"] != req["executor_id"]
            or outcome["capability_id"] != req["capability_id"]
            or outcome["evidence_contract"] != binding.get("expected_evidence_contract")
        ):
            raise OrchestrationError("aggregation_identity_mismatch")

        st = outcome.get("status")
        if st == "succeeded":
            succeeded += 1
        elif st == "failed":
            failed += 1
        else:
            raise OrchestrationError("dispatch_outcome_status_invalid")

        item_count = outcome.get("result_item_count", 0)
        total_items += item_count
        arts = outcome.get("evidence_artifacts", [])
        op_warnings = list(outcome.get("warnings", []))
        aggregate_warnings.extend(op_warnings)

        op_receipts.append({
            "operation_id": op_id,
            "executor_id": outcome["executor_id"],
            "capability_id": outcome["capability_id"],
            "status": st,
            "error_code": outcome.get("error_code"),
            "execution_request_id": outcome["execution_request_id"],
            "execution_request_hash": outcome["execution_request_hash"],
            "result_item_count": item_count,
            "evidence_artifacts": arts,
            "warnings": op_warnings,
        })

        bundle_entries.append({
            "operation_id": op_id,
            "status": st,
            "error_code": outcome.get("error_code"),
            "result_item_count": item_count,
            "artifacts": [
                {
                    "relative_path": a["relative_path"],
                    "sha256": a["sha256"],
                    "schema_version": a["schema_version"],
                    "byte_size": a["byte_size"],
                    "item_count": a["item_count"],
                }
                for a in arts
            ],
            "warnings": op_warnings,
        })

        for a in arts:
            artifact_inventory.append({
                "relative_path": a["relative_path"],
                "sha256": a["sha256"],
                "schema_version": a["schema_version"],
                "byte_size": a["byte_size"],
                "item_count": a["item_count"],
                "evidence_contract": outcome["evidence_contract"],
            })

    if set(approved_order) != seen_ops:
        raise OrchestrationError("operation_missing")

    if succeeded == total_ops:
        overall_status = "succeeded"
    elif succeeded > 0:
        overall_status = "partial_success"
    else:
        overall_status = "failed"

    return {
        "overall_status": overall_status,
        "total_operations": total_ops,
        "succeeded_operations": succeeded,
        "failed_operations": failed,
        "operation_receipts": op_receipts,
        "operation_evidence_entries": bundle_entries,
        "artifact_inventory": artifact_inventory,
        "total_item_count": total_items,
        "warnings": aggregate_warnings,
    }
