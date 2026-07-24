"""Owner-initiated finite execution orchestrator for immutable 05B artifacts."""
from __future__ import annotations

from pathlib import Path

from scripts.m8r_filesystem_safety import FilesystemSafetyError, atomic_write_text

from .authorization_gate import approved_operation_map, authorize
from .canonical import canonical_json, receipt_id
from .consumption_store import ConsumptionStore
from .errors import OrchestrationError
from .evidence_aggregation import aggregate
from .executor_dispatch import dispatch
from .receipt import build_receipt
from .registry import ExecutorRegistry


def execute_controlled_plan(plan: dict, authorization: dict, consumption_binding: dict, *, supplied_consumption_state: dict, execution_timestamp: str, output_root: str | Path, executor_registry: ExecutorRegistry | None = None, finished_timestamp: str | None = None) -> dict:
    """Claim once, invoke the exact approved operations, then finalize the claim.

    `execution_timestamp` is intentionally caller-supplied: no scheduler, wall-clock
    identity, or implicit retry is introduced by this layer.
    """
    if not isinstance(execution_timestamp, str) or not execution_timestamp.endswith("Z"):
        raise OrchestrationError("execution_timestamp_invalid")
    finished_timestamp = finished_timestamp or execution_timestamp
    authorize(plan, authorization, consumption_binding, evaluation_timestamp=execution_timestamp, supplied_consumption_state=supplied_consumption_state)
    bindings = approved_operation_map(plan, authorization)
    registry = executor_registry or ExecutorRegistry()
    receipt_identifier = receipt_id(authorization_id=authorization["authorization_id"], authorization_hash=authorization["authorization_hash"], plan_hash=plan["plan_hash"], execution_timestamp=execution_timestamp)
    store = ConsumptionStore(output_root)
    store.claim(consumption_binding, claimed_at=execution_timestamp, receipt_id=receipt_identifier)
    results = dispatch(plan=plan, authorization=authorization, approved_bindings=bindings, registry=registry, execution_timestamp=execution_timestamp)
    bundle = aggregate(plan, authorization, results)
    receipt = build_receipt(plan, authorization, consumption_binding, execution_timestamp=execution_timestamp, finished_timestamp=finished_timestamp, operation_results=results, bundle=bundle)
    try:
        root = Path(output_root)
        atomic_write_text(root, Path("receipts") / f"{receipt_identifier}.json", canonical_json(receipt) + "\n", allow_overwrite=False)
        atomic_write_text(root, Path("bundles") / f"{receipt_identifier}.json", canonical_json(bundle) + "\n", allow_overwrite=False)
        store.finalize(consumption_binding, claimed_at=execution_timestamp, finished_at=finished_timestamp, receipt_id=receipt_identifier, execution_status=bundle["status"])
    except FilesystemSafetyError as exc:
        # The claim remains present, deliberately preventing a retry after an uncertain write.
        raise OrchestrationError(exc.code) from exc
    return {"execution_receipt": receipt, "evidence_bundle": bundle, "consumption_state": "consumed"}
