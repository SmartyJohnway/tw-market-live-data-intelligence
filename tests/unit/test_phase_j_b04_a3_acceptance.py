from __future__ import annotations

import copy

import pytest

from scripts.validate_phase_j_b04_a3_network_free_implementation import (
    RECORD,
    _load,
    validate_contract,
)


def test_a3_acceptance_record_passes_machine_contract() -> None:
    record = _load(RECORD)
    assert validate_contract(record)["status"] == "PASS"


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("canonical_h2_runtime", "ACTIVE"),
        ("canonical_h2_selected_executor", "phase_h_h2_twse_exright_pre_executor"),
        ("h2_max_gets", 2),
        ("h2_retry_count", 1),
        ("twt49u_required", True),
        ("h2_historical_completeness_claimed", True),
        ("no_row_proves_historical_no_event", True),
        ("scheduled_promoted_to_effective", True),
        ("local_reference_calculation_allowed", True),
        ("h3_dependency_required", False),
        ("cross_target_dependency_allowed", True),
        ("dependency_artifact_identity_required", False),
        ("hidden_h2_acquisition_allowed", True),
        ("h4_semantics_modified", True),
        ("result_v3_schema_changed", True),
        ("audit_v3_schema_changed", True),
        ("phase_j", "STARTED"),
        ("j_b04", "CLOSED"),
        ("mcp_tool_count", 7),
        ("market_GETs", 1),
        ("market_HEADs", 1),
        ("market_POSTs", 1),
    ],
)
def test_a3_validator_rejects_unsafe_mutations(key: str, value: object) -> None:
    record = copy.deepcopy(_load(RECORD))
    record["machine_assertions"][key] = value
    with pytest.raises(AssertionError):
        validate_contract(record)
