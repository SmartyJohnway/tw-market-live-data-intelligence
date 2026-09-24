"""Focused fixture-only tests for the dormant deterministic H3 evidence core."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, FormatChecker

from scripts.validate_phase_h_v3_contracts import validate_recent_performance_semantics
from server.services.phase_h_discontinuity_safety import derive_discontinuity_safety
from server.services.phase_h_recent_performance import H3DerivationError, build_recent_performance_evidence


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = json.loads((ROOT / "schemas/recent_performance_evidence.v1.schema.json").read_text(encoding="utf-8"))
TARGET = {"canonical_target_id": "TWSE:2330", "market": "TWSE", "security_code": "2330"}


def row(index: int, *, close: float | None = None, volume: int | None = None, day_step: int = 2) -> dict:
    return {
        **TARGET,
        "trade_date": (date(2026, 8, 1) + timedelta(days=index * day_step)).isoformat(),
        "close": 100 + index if close is None else close,
        "volume": 1000 + index if volume is None else volume,
        "source_family": "OFFICIAL_FIXTURE_ONLY",
        "source_contract_id": "fixture-h3-contract",
        "retrieved_at": "2026-09-24T00:00:00Z",
        "citation_ids": [f"cit-h3-{index:02d}"],
    }


def end_after(index: int, *, close: float = 150, volume: int | None = 1500) -> dict:
    return {
        **TARGET,
        "trade_date": (date(2026, 8, 1) + timedelta(days=(index + 1) * 2)).isoformat(),
        "close": close,
        "volume": volume,
        "source_family": "OFFICIAL_FIXTURE_ONLY",
        "source_contract_id": "fixture-h3-contract",
        "retrieved_at": "2026-09-24T00:00:00Z",
        "citation_ids": ["cit-h3-end"],
    }


def build(
    count: int,
    *,
    requested: int | None = None,
    lookbacks: tuple[int, ...] | None = None,
    rows: list[dict] | None = None,
    end: dict | None = None,
    current_volume_basis: str = "completed_session",
    historical_average_evidence: dict | None = None,
    governed_outcome: str | None = None,
    caveats: tuple[str, ...] = (),
) -> dict:
    requested = count if requested is None else requested
    return build_recent_performance_evidence(
        target=TARGET,
        observations=[row(i) for i in range(count)] if rows is None else rows,
        governed_end_observation=end_after(count - 1) if end is None and count else end,
        requested_observations=requested,
        baseline_lookbacks=lookbacks or (requested,),
        current_volume_basis=current_volume_basis,
        historical_average_evidence=historical_average_evidence,
        governed_outcome=governed_outcome,
        caveats=caveats,
        schema=SCHEMA,
    )


def assert_valid(value: dict) -> None:
    assert not list(Draft7Validator(SCHEMA, format_checker=FormatChecker()).iter_errors(value))
    validate_recent_performance_semantics(value)


@pytest.mark.parametrize("lookback", [1, 5, 20])
def test_full_baselines_use_exact_n_plus_one_closes_and_validate(lookback: int) -> None:
    result = build(lookback)
    assert_valid(result)
    baseline = result["baselines"][0]
    assert baseline["status"] == "available"
    assert baseline["required_distinct_close_count"] == lookback + 1
    assert baseline["actual_distinct_close_count"] == lookback + 1
    assert result["valid_observation_count"] == lookback
    assert result["governed_end_observation"]["trade_date"] not in {item["trade_date"] for item in result["observations"]}


def test_sorts_deduplicates_and_bounds_extra_observation_history() -> None:
    source_rows = [row(i) for i in range(24)]
    source_rows.extend([deepcopy(source_rows[8])])
    result = build(20, rows=list(reversed(source_rows)), end=end_after(23))
    assert_valid(result)
    assert result["valid_observation_count"] == 20
    assert len(result["observations"]) == 20
    assert [item["trade_date"] for item in result["observations"]] == sorted(item["trade_date"] for item in result["observations"])
    assert result["observations"][0]["trade_date"] == row(4)["trade_date"]
    assert result["observations"][-1]["trade_date"] == row(23)["trade_date"]


def test_semantically_identical_duplicate_is_deduplicated() -> None:
    duplicate = row(0)
    duplicate["citation_ids"] = list(reversed(duplicate["citation_ids"]))
    result = build(1, rows=[row(0), duplicate])
    assert_valid(result)
    assert result["valid_observation_count"] == 1


def test_conflicting_same_date_record_fails_closed() -> None:
    conflict = row(0)
    conflict["close"] += 1
    with pytest.raises(H3DerivationError, match="conflicting_duplicate_trade_date"):
        build(1, rows=[row(0), conflict])


def test_target_mismatch_and_governed_end_duplication_fail_closed() -> None:
    mismatch = row(0)
    mismatch["security_code"] = "0050"
    with pytest.raises(H3DerivationError, match="target_identity_mismatch"):
        build(1, rows=[mismatch])
    with pytest.raises(H3DerivationError, match="governed_end_must_be_separate"):
        build(1, rows=[row(0)], end=row(0))


def test_invalid_end_chronology_fails_closed() -> None:
    bad_end = end_after(0)
    bad_end["trade_date"] = "2026-08-02"
    with pytest.raises(H3DerivationError, match="governed_end_chronology_invalid"):
        build(2, rows=[row(0), row(1)], end=bad_end)


def test_raw_return_arithmetic_and_completed_close_range() -> None:
    result = build(1, rows=[row(0, close=100)], end=end_after(0, close=125))
    assert_valid(result)
    assert result["baselines"][0]["recent_return_pct"] == 25
    assert result["baselines"][0]["return_basis"] == "raw_unadjusted_close_to_close"
    assert result["recent_close_range"] == {
        "range_basis": "completed_session_closing_price",
        "recent_close_high": 125,
        "recent_close_low": 100,
    }


def test_zero_start_close_fails_closed_for_return_calculation() -> None:
    with pytest.raises(H3DerivationError, match="baseline_start_close_invalid"):
        build(1, rows=[row(0, close=0)], end=end_after(0, close=100))


def test_intraday_volume_alignment_and_caller_governed_eod_average() -> None:
    intraday = build(1, current_volume_basis="intraday_cumulative")
    assert_valid(intraday)
    assert intraday["volume_context"]["comparison_alignment"] == "partial_session_vs_completed_sessions"
    assert intraday["volume_context"]["historical_average_volume"] is None

    average = {
        "target": dict(TARGET),
        "historical_average_basis": "completed_official_sessions",
        "value": 1010,
        "source_family": "OFFICIAL_FIXTURE_ONLY",
        "source_contract_id": "fixture-volume-average-contract",
        "retrieved_at": "2026-09-24T00:00:00Z",
        "citation_ids": ["cit-volume-average"],
    }
    eod = build(1, historical_average_evidence=average)
    assert_valid(eod)
    assert eod["volume_context"]["comparison_alignment"] == "aligned"
    assert eod["volume_context"]["historical_average_volume"] == 1010
    assert "cit-volume-average" in eod["citation_ids"]


def test_unavailable_volume_context_is_not_fabricated() -> None:
    result = build(1, current_volume_basis="completed_session")
    assert_valid(result)
    assert result["volume_context"]["comparison_alignment"] == "unavailable"
    assert result["volume_context"]["historical_average_volume"] is None


def test_historical_average_requires_exact_target_and_completed_session_basis() -> None:
    evidence = {
        "target": dict(TARGET),
        "historical_average_basis": "completed_official_sessions",
        "value": 1010,
        "source_family": "OFFICIAL_FIXTURE_ONLY",
        "source_contract_id": "fixture-volume-average-contract",
        "retrieved_at": "2026-09-24T00:00:00Z",
        "citation_ids": ["cit-volume-average"],
    }
    accepted = build(1, historical_average_evidence=evidence)
    assert_valid(accepted)
    assert accepted["volume_context"]["historical_average_volume"] == 1010

    wrong_target = deepcopy(evidence)
    wrong_target["target"]["security_code"] = "0050"
    with pytest.raises(H3DerivationError, match="historical_average_target_mismatch"):
        build(1, historical_average_evidence=wrong_target)

    wrong_basis = deepcopy(evidence)
    wrong_basis["historical_average_basis"] = "intraday_cumulative"
    with pytest.raises(H3DerivationError, match="invalid_historical_average_basis"):
        build(1, historical_average_evidence=wrong_basis)

    missing_basis = deepcopy(evidence)
    del missing_basis["historical_average_basis"]
    with pytest.raises(H3DerivationError, match="invalid_historical_average_evidence"):
        build(1, historical_average_evidence=missing_basis)


def test_partial_twenty_observations_keeps_valid_shorter_baseline() -> None:
    result = build(8, requested=20, lookbacks=(5, 20))
    assert_valid(result)
    assert result["coverage_status"] == "partial"
    assert result["requested_observations"] == 20
    assert result["valid_observation_count"] == 8
    assert result["missing_observation_count"] == 12
    assert result["available_baselines"] == [5]
    assert result["baselines"][1]["status"] == "insufficient_coverage"


def test_requested_baseline_cannot_be_omitted() -> None:
    with pytest.raises(H3DerivationError, match="requested_baseline_missing"):
        build(20, requested=20, lookbacks=(5,))


def test_requested_twenty_day_baseline_alone_is_available() -> None:
    result = build(20, requested=20, lookbacks=(20,))
    assert_valid(result)
    assert result["coverage_status"] == "complete"
    assert result["available_baselines"] == [20]


def test_insufficient_coverage_with_no_available_baseline() -> None:
    result = build(3, requested=5, lookbacks=(5,))
    assert_valid(result)
    assert result["coverage_status"] == "insufficient"
    assert result["available_baselines"] == []
    assert result["unavailable_baselines"] == [5]


def test_unavailable_source_failed_and_binding_failed_states_remain_distinct() -> None:
    unavailable = build(0, requested=5, lookbacks=(5,), end=None)
    assert_valid(unavailable)
    assert unavailable["coverage_status"] == "unavailable"

    for state in ("source_failed", "binding_failed"):
        failed = build(0, requested=5, lookbacks=(5,), end=None, governed_outcome=state, caveats=(f"fixture:{state}",))
        assert_valid(failed)
        assert failed["coverage_status"] == state
        assert failed["caveats"] == [f"fixture:{state}"]
    for state in ("unsupported", "not_applicable"):
        value = build(0, requested=5, lookbacks=(5,), end=None, governed_outcome=state)
        assert_valid(value)
        assert value["coverage_status"] == state


@pytest.mark.parametrize(
    ("rows", "end", "outcome"),
    [
        ([row(0, close=0)], end_after(0), None),
        ([row(0, volume=-1)], end_after(0), None),
        ([{**row(0), "citation_ids": []}], end_after(0), None),
    ],
)
def test_invalid_close_volume_and_provenance_fail_closed(rows, end, outcome) -> None:
    with pytest.raises(H3DerivationError):
        build(1, rows=rows, end=end, governed_outcome=outcome)


def test_invalid_lookback_and_average_provenance_fail_closed() -> None:
    with pytest.raises(H3DerivationError, match="invalid_baseline_lookback"):
        build(1, lookbacks=(0,))
    with pytest.raises(H3DerivationError, match="invalid_historical_average_evidence"):
        build(1, historical_average_evidence={"value": 10})


def test_generated_h3_baseline_window_is_consumed_by_h4() -> None:
    generated = build(1, rows=[row(0, close=100)], end=end_after(0, close=101))
    h2 = json.loads((ROOT / "tests/fixtures/phase_h_contract_v3/contract_examples.json").read_text(encoding="utf-8"))["h2_preannouncement_and_final"]
    h2 = deepcopy(h2)
    start = generated["baselines"][0]["start_observation_date"]
    end = generated["baselines"][0]["end_observation_date"]
    h2["status"] = "no_evidence_in_covered_scope"
    h2["events"] = []
    h2["coverage"].update({
        "status": "complete",
        "declared_scope_complete": True,
        "retrieval_succeeded": True,
        "source_contract_validated": True,
        "exact_target_search_succeeded": True,
        "requested_window": {"start": start, "end": end},
        "declared_event_subtypes": ["ex_dividend"],
        "covered_event_subtypes": ["ex_dividend"],
        "uncovered_event_subtypes": [],
        "failed_source_families": [],
    })
    result = derive_discontinuity_safety(
        h2_evidence=h2,
        h3_evidence=generated,
        h2_evidence_reference="fixture-h2-generated-window",
        h3_evidence_reference="fixture-h3-builder-output",
    )
    assert result["comparison_window"]["start_observation_date"] == start
    assert result["comparison_window"]["end_observation_date"] == end
    assert result["state"] == "no_material_discontinuity_detected"
