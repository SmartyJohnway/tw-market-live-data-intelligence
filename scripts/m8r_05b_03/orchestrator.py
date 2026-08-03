"""End-to-end controlled plan execution entry point for M8R-05B-03."""
from __future__ import annotations

from typing import Any

from .controlled_dispatch import claim_and_dispatch_approved
from .dispatch import RuntimeAdapterRegistry
from .evidence_aggregation import aggregate_dispatch_outcomes
from .receipt import finalize_consumption_and_write_receipt


def execute_controlled_plan(
    plan: dict[str, Any],
    authorization: dict[str, Any],
    consumption_binding: dict[str, Any],
    *,
    supplied_consumption_state: dict[str, Any],
    accepted_preflight: dict[str, Any],
    evaluation_timestamp: str,
    claim_created_at: str,
    finalized_at: str,
    executor_registry_metadata: dict[str, Any],
    runtime_adapter_registry: RuntimeAdapterRegistry,
    output_root: str,
    mode: str,
    confirm_execution: bool = False,
    operator_confirmation_reference: str | None = None,
    confirm_network_execution: bool = False,
) -> dict[str, Any]:
    dispatch_res = claim_and_dispatch_approved(
        plan,
        authorization,
        consumption_binding,
        supplied_consumption_state=supplied_consumption_state,
        accepted_preflight=accepted_preflight,
        evaluation_timestamp=evaluation_timestamp,
        claim_created_at=claim_created_at,
        executor_registry_metadata=executor_registry_metadata,
        runtime_adapter_registry=runtime_adapter_registry,
        output_root=output_root,
        mode=mode,
        confirm_execution=confirm_execution,
        operator_confirmation_reference=operator_confirmation_reference,
        confirm_network_execution=confirm_network_execution,
    )

    aggregation = aggregate_dispatch_outcomes(
        accepted_preflight,
        dispatch_res["dispatch_outcomes"],
    )

    if mode == "execute-approved":
        final_claim, receipt, bundle = finalize_consumption_and_write_receipt(
            accepted_preflight,
            dispatch_res["claim_record"],
            dispatch_res["claim_relative_path"],
            aggregation,
            output_root=output_root,
            finalized_at=finalized_at,
        )
        return {
            "schema_version": "m8r_05b_03_controlled_execution_result.v1",
            "mode": mode,
            "claim_relative_path": dispatch_res["claim_relative_path"],
            "claim_record": final_claim,
            "dispatch_outcomes": dispatch_res["dispatch_outcomes"],
            "aggregation": aggregation,
            "execution_receipt": receipt,
            "evidence_bundle": bundle,
            "consumption_state": final_claim["state"],
            "aggregation_created": True,
            "execution_receipt_created": True,
        }
    else:
        return {
            "schema_version": "m8r_05b_03_controlled_execution_result.v1",
            "mode": mode,
            "claim_relative_path": None,
            "claim_record": None,
            "dispatch_outcomes": dispatch_res["dispatch_outcomes"],
            "aggregation": aggregation,
            "execution_receipt": None,
            "evidence_bundle": None,
            "consumption_state": "unconsumed_dry_run",
            "aggregation_created": True,
            "execution_receipt_created": False,
        }
