"""Offline verification of the committed bounded L01-L08 live ledger."""

from __future__ import annotations

import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/acceptance_runs/phase_g_pr_d_controlled_live.json"


def _report() -> dict:
    return json.loads(REPORT.read_text(encoding="utf-8"))


def test_l01_l08_each_have_at_least_one_truthful_pass():
    report = _report()
    assert report["status"] == "PASS"
    assert set(report["cases"]) == {f"L{index:02d}" for index in range(1, 9)}
    assert all(item["status"] == "PASS" for item in report["cases"].values())
    assert report["network_summary"] == {
        "bounded_attempt_count": 23,
        "full_market_payload_persisted": False,
        "target_bounded_governed_artifacts_only": True,
    }
    assert report["controlled_live_identity_authority"] == {
        "type": "acceptance-local qualified Security Master subset",
        "included_targets": ["TWSE:2330", "TPEX:6488", "TWSE:0050"],
        "official_security_master_acquisition_bootstrap_proven": False,
        "scope_note": "This controlled acceptance did not re-prove official Security Master acquisition/bootstrap and does not replace earlier Security Master lifecycle acceptance.",
    }


def test_selected_twse_tpex_and_v1_runs_are_full_success_v2_packages():
    report = _report()
    runs = report["selected_passing_runs"]
    assert set(runs) == {"TWSE:2330", "TPEX:6488", "V1:TWSE:2330"}
    for run in runs.values():
        assert run["result"]["status"] == "full_success"
        assert run["result"]["schema_version"] == "unified_market_evidence_result.v2"
        assert run["audit"]["schema_version"] == "unified_market_evidence_audit_package.v2"
        assert run["citation_graph_clean"] is True
        assert run["target_bounded_persistence"] is True
    assert runs["V1:TWSE:2330"]["result"]["request_schema_version"] == "unified_market_evidence_request.v1"


def test_selected_research_sources_are_real_primary_csv_and_monthly_values_available():
    runs = _report()["selected_passing_runs"]
    for target in ("TWSE:2330", "TPEX:6488"):
        research = runs[target]["research"]
        assert research["material_disclosures"]["status"] == "no_evidence_in_covered_scope"
        assert research["monthly_revenue"]["status"] == "available"
        assert research["monthly_revenue"]["value_present"] is True
        for evidence in research.values():
            assert evidence["source"]["transport"] == "official_csv"
            assert evidence["source"]["fallback_used"] is False
            assert evidence["source"]["fallback_attempted"] is False
            assert evidence["target"]["canonical_target_id"] == target


def test_live_ledger_preserves_transient_failures_without_paths_or_secrets():
    report = _report()
    assert len(report["attempt_history"]) == 4
    assert "transient" in report["transient_source_observation"].lower()
    text = REPORT.read_text(encoding="utf-8")
    assert re.search(r"[A-Za-z]:\\", text) is None
    lowered = text.lower()
    for forbidden in ("password", "private_key", "bearer ", "authorization_cookie"):
        assert forbidden not in lowered
    assert report["unauthorized_persistence"] == "NONE"
    assert report["scheduler_polling_background"] == "NONE"
