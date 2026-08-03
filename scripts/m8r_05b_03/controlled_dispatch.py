"""Commit 2 orchestration: revalidate, atomically claim (execute-approved only), then dispatch."""
from __future__ import annotations

from .consumption_claim import atomic_claim_authorization, validate_claim_destination
from .dispatch import RuntimeAdapterRegistry, dispatch_prepared, prepare_dispatch
from .errors import OrchestrationError
from .preflight import (
    build_orchestrator_preflight,
    validate_accepted_preflight,
)
from .registry import ExecutorMetadataRegistry


def claim_and_dispatch_approved(
    plan: dict,
    authorization: dict,
    consumption_binding: dict,
    *,
    supplied_consumption_state: dict,
    accepted_preflight: dict,
    evaluation_timestamp: str,
    claim_created_at: str,
    executor_registry_metadata: dict,
    runtime_adapter_registry: RuntimeAdapterRegistry,
    output_root: str,
    mode: str,
    confirm_execution: bool = False,
    operator_confirmation_reference: str | None = None,
    confirm_network_execution: bool = False,
) -> dict:
    if mode not in {"dry-run", "execute-approved"}:
        raise OrchestrationError("execution_mode_invalid")

    rebuilt_preflight = build_orchestrator_preflight(
        plan,
        authorization,
        consumption_binding,
        supplied_consumption_state=supplied_consumption_state,
        evaluation_timestamp=evaluation_timestamp,
        executor_registry_metadata=executor_registry_metadata,
        output_root=output_root,
    )
    validate_accepted_preflight(accepted_preflight, rebuilt_preflight)
    metadata_registry = ExecutorMetadataRegistry.from_json(executor_registry_metadata)
    prepared = prepare_dispatch(
        accepted_preflight,
        metadata_registry,
        runtime_adapter_registry,
        mode=mode,
    )
    validate_claim_destination(output_root, accepted_preflight["authorization_id"])

    if mode == "execute-approved":
        if confirm_execution is not True:
            raise OrchestrationError("execution_confirmation_required")
        if not isinstance(operator_confirmation_reference, str) or not operator_confirmation_reference.strip():
            raise OrchestrationError("operator_confirmation_reference_required")
        if accepted_preflight.get("network_required") and confirm_network_execution is not True:
            raise OrchestrationError("network_execution_confirmation_required")

        claim_record, claim_path = atomic_claim_authorization(
            accepted_preflight,
            supplied_consumption_state,
            output_root=output_root,
            claim_created_at=claim_created_at,
        )
        consumption_state = "claimed"
    else:
        claim_record = None
        claim_path = None
        consumption_state = "unconsumed_dry_run"

    outcomes = dispatch_prepared(
        prepared,
        governed_output_root=accepted_preflight["governed_output_root"],
        mode=mode,
    )
    return {
        "schema_version": "m8r_05b_03_claim_and_dispatch_result.v1",
        "mode": mode,
        "claim_relative_path": claim_path,
        "claim_record": claim_record,
        "dispatch_outcomes": outcomes,
        "consumption_state": consumption_state,
        "aggregation_created": False,
        "execution_receipt_created": False,
    }
