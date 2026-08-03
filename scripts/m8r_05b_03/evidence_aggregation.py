"""Commit 3 evidence aggregation: collect adapter dispatch outcomes and compute overall status."""
from __future__ import annotations

from typing import Any

from .canonical import sha256_json
from .errors import OrchestrationError


def aggregate_dispatch_outcomes(
    preflight: dict,
    dispatch_outcomes: list[dict[str, Any]],
) -> dict[str, Any]:
    if not isinstance(dispatch_outcomes, list) or not dispatch_outcomes:
        raise OrchestrationError("dispatch_outcomes_empty")

    total_ops = len(preflight["approved_operation_order"])
    if len(dispatch_outcomes) != total_ops:
        raise OrchestrationError("dispatch_outcomes_count_mismatch")

    requests = preflight.get("bounded_execution_requests", [])
    requests_by_op = {r.get("operation_id"): r for r in requests if isinstance(r, dict)}

    succeeded = 0
    failed = 0
    op_receipts = []

    for outcome in dispatch_outcomes:
        st = outcome.get("status")
        if st == "succeeded":
            succeeded += 1
        elif st == "failed":
            failed += 1
        else:
            raise OrchestrationError("dispatch_outcome_status_invalid")

        op_id = outcome["operation_id"]
        req = outcome.get("request") or requests_by_op.get(op_id, {})
        req_hash = req.get("execution_request_hash") or sha256_json(req)
        req_id = req.get("execution_request_id") or ("umereq-v1-" + req_hash[:20])
        cap_id = outcome.get("capability_id") or req.get("capability_id", "unknown_capability")
        exec_id = outcome.get("executor_id") or req.get("executor_id", "unknown_executor")
        art_path = outcome.get("artifact_relative_path") or req.get("relative_contained_output_path")

        op_receipts.append({
            "operation_id": op_id,
            "executor_id": exec_id,
            "capability_id": cap_id,
            "status": st,
            "error_code": outcome.get("error_code"),
            "execution_request_id": req_id,
            "execution_request_hash": req_hash,
            "result_item_count": outcome.get("result_item_count", 0),
            "artifact_relative_path": art_path if st == "succeeded" else None,
        })

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
    }
