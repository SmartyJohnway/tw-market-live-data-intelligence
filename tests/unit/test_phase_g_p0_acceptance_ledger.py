"""Validate that the PR-D D1 ledger accounts for every frozen P0 case."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs/acceptance_runs/phase_g_pr_d_p0_ledger.json"


def test_phase_g_d1_ledger_has_exactly_all_74_p0_cases_and_no_p1_claims():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    cases = ledger["cases"]
    expected = {
        *(f"A{index:02d}" for index in range(1, 13)),
        *(f"B{index:02d}" for index in range(1, 11)),
        *(f"C{index:02d}" for index in range(1, 17)),
        *(f"D{index:02d}" for index in range(1, 15)),
        *(f"E{index:02d}" for index in range(1, 13)),
        *(f"F{index:02d}" for index in range(1, 11)),
    }
    assert len(expected) == ledger["expected_case_count"] == len(cases) == 74
    assert set(cases) == expected
    assert ledger["status"] == "PASS"
    assert ledger["network_activity"] is False
    assert not any(case_id.startswith("L") for case_id in cases)
    assert all(isinstance(reference, str) and reference for reference in cases.values())
