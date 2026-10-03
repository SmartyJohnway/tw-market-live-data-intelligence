"""Pure future evidence attribution; no transport, reservation or persistence."""
from __future__ import annotations


def source_findings(result: dict | None, *, complete_body_received: bool) -> dict:
    if not complete_body_received:
        if result is not None:
            raise ValueError("partial_payload_semantics_forbidden")
        return {"evaluation_status": "NOT_EVALUATED", "target_binding": None,
                "whole_dataset_arithmetic": None, "unit_proof": None,
                "normalized_observation": None, "batching_observation": "NOT_EVALUATED"}
    if result is None:
        raise ValueError("evaluated_result_required")
    count = result["exact_matches"]
    if type(count) is not int or count < 0:
        raise ValueError("invalid_exact_match_count")
    return {"evaluation_status": "EVALUATED", "target_binding": count,
            "whole_dataset_arithmetic": result["arithmetic"],
            "unit_proof": result["unit"], "normalized_observation": result["observation"],
            "batching_observation": "PROVEN" if result["whole_market_payload"] is True else "NOT_PROVEN"}


def batching_findings(sources: dict, prior_evidence_refs: list[str]) -> dict:
    observed = {market: value["batching_observation"] for market, value in sources.items()}
    return {"batching_observation": observed,
            "mixed_market_observation": "PROVEN" if set(observed) == {"TWSE", "TPEx"}
            and all(value == "PROVEN" for value in observed.values()) else "NOT_EVALUATED",
            "batching_contract_support": {"prior_evidence_refs": list(prior_evidence_refs)}}
