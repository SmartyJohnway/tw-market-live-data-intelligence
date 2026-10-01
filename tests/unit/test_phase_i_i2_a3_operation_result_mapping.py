from __future__ import annotations

import copy
import json

import pytest

from scripts.m8r_05c.citation_builder import _build_citation_id
from scripts.run_phase_i_i2_a3_bounded_live_acceptance import (
    _operation_result_status,
    deterministic_fixture_payload,
)
from server.services.phase_i_i2_index_futures_adapters import normalize_taifex_tx_payload


def _rows_for_status(status: str) -> list[dict]:
    rows = json.loads(deterministic_fixture_payload())
    if status == "partial":
        next(row for row in rows if row["Date"] == "20260929" and row["ContractMonth(Week)"] == "202610")["Open"] = "-"
    elif status == "unavailable":
        for row in rows:
            if row["Date"] == "20260929" and row["Contract"] == "TX" and row["TradingSession"] == "一般":
                row["Contract"] = "MTX"
    elif status == "source_failed":
        next(row for row in rows if row["Date"] == "20260929" and row["Contract"] == "TX"
             and row["TradingSession"] == "一般" and row["ContractMonth(Week)"] == "202610")["Last"] = "malformed"
    elif status == "binding_failed":
        selected = next(row for row in rows if row["Date"] == "20260929" and row["Contract"] == "TX"
                        and row["TradingSession"] == "一般" and row["ContractMonth(Week)"] == "202610")
        rows.append(copy.deepcopy(selected))
    return rows


@pytest.mark.parametrize(
    "evidence_status,expected_operation_status,error_code",
    [
        ("complete", "succeeded", None),
        ("partial", "succeeded", None),
        ("unavailable", "succeeded", None),
        ("source_failed", "failed", "source_failed"),
        ("binding_failed", "failed", "binding_failed"),
    ],
)
def test_evidence_status_maps_to_accepted_operation_result_semantics(
    evidence_status, expected_operation_status, error_code
):
    operation_id = "umeop-op-v1-" + "a" * 20
    evidence = normalize_taifex_tx_payload(
        _rows_for_status(evidence_status),
        governed_retrieved_at="2026-10-01T00:00:00Z",
        fmtqik_benchmark_date=None,
        citation_ids=[_build_citation_id(operation_id, f"evidence/phase_i/i2/{operation_id}.json")],
    )
    assert evidence["status"] == evidence_status
    assert _operation_result_status(evidence_status) == (expected_operation_status, error_code)


def test_unrecognized_evidence_status_fails_closed():
    with pytest.raises(RuntimeError, match="evidence_status_unrecognized"):
        _operation_result_status("unknown")
