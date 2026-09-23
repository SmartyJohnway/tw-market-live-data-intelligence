from __future__ import annotations

import json
from pathlib import Path

import pytest

import scripts.run_phase_h_h_sb1_h2_source_live_acceptance as runner


PRE_ROW = {
    "SecuritiesCompanyCode": "6488",
    "ExRrightsExDividendDate": "2026-08-20",
    "ExRrightsExDividend": "除息",
    "CashDividend": "1",
    "StockDividendRatio": "0",
    "SubscriptionRatioToNewSharesIssued": "0",
    "SubscriptionPricePerShare": "",
}
FINAL_ROW = {
    "SecuritiesCompanyCode": "6488",
    "Date": "2026-08-20",
    "ClosePriceBeforeExRightsDiviend": "100",
    "ExRightsDiviendQuote": "95",
    "CashDividend": "2.5",
    "StockDividend": "0",
    "ExRightsDiviend": "0",
    "OpeningReferencePrice": "95",
    "SubscriptionPricePerShare": "",
}
OTHER_PRE = {
    **PRE_ROW,
    "SecuritiesCompanyCode": "9999",
    "CashDividend": "must-not-persist",
}
OTHER_FINAL = {
    **FINAL_ROW,
    "SecuritiesCompanyCode": "9999",
    "CashDividend": "must-not-persist",
}


def test_h_sb1_a0_requires_owner_authorization(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("H_SB1_H2_OWNER_AUTHORIZED", raising=False)
    with pytest.raises(RuntimeError, match="owner_authorization_environment_missing"):
        runner.run(tmp_path)


def test_h_sb1_a0_calls_exact_two_sources_and_persists_only_target_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("H_SB1_H2_OWNER_AUTHORIZED", "YES")
    calls: list[tuple[str, int]] = []

    def fake_fetch(url: str, *, timeout: int) -> bytes:
        calls.append((url, timeout))
        if url == runner.PRE_URL:
            rows = [PRE_ROW, OTHER_PRE]
        elif url == runner.FINAL_URL:
            rows = [FINAL_ROW, OTHER_FINAL]
        else:
            raise AssertionError("unexpected endpoint")
        return json.dumps(rows, ensure_ascii=False).encode("utf-8")

    monkeypatch.setattr(runner.production, "_fetch_official_payload", fake_fetch)
    report = runner.run(tmp_path)

    assert report["status"] == "PASS"
    assert report["target"] == runner.TARGET
    assert calls == [(runner.PRE_URL, 15), (runner.FINAL_URL, 15)]
    assert report["network"]["actual_call_count"] == 2
    assert report["network"]["retry_count"] == 0
    assert report["network"]["raw_full_market_payload_persisted"] is False
    assert [item["source_id"] for item in report["source_results"]] == [
        runner.PRE_SOURCE_ID,
        runner.FINAL_SOURCE_ID,
    ]
    assert [item["status"] for item in report["source_results"]] == ["available", "available"]
    assert all(item["activation_state"] == "eligible" for item in report["source_results"])
    assert all(item["matched_event_count"] == 1 for item in report["source_results"])
    assert report["production_claims"] == {
        "corporate_action_context_materialized": False,
        "requested_window_bound": False,
        "production_executor_registered": False,
        "route_activation_effective": False,
        "catalog_or_routing_changed": False,
        "h3_implementation_started": False,
    }

    files = sorted(path.name for path in tmp_path.iterdir())
    assert files == ["H_SB1_A0_H2_SOURCE_LIVE_REPORT.json"]
    persisted = (tmp_path / files[0]).read_text(encoding="utf-8")
    assert "must-not-persist" not in persisted
    assert '"canonical_target_id": "TPEX:6488"' in persisted


def test_h_sb1_a0_accepts_truthful_no_row_without_claiming_activation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("H_SB1_H2_OWNER_AUTHORIZED", "YES")
    monkeypatch.setattr(
        runner.production,
        "_fetch_official_payload",
        lambda _url, *, timeout: json.dumps(
            [{**PRE_ROW, "SecuritiesCompanyCode": "9999"}]
            if _url == runner.PRE_URL
            else [{**FINAL_ROW, "SecuritiesCompanyCode": "9999"}],
            ensure_ascii=False,
        ).encode("utf-8"),
    )

    report = runner.run(tmp_path)

    assert [item["status"] for item in report["source_results"]] == [
        "no_evidence_in_covered_scope",
        "no_evidence_in_covered_scope",
    ]
    assert all(item["matched_event_count"] == 0 for item in report["source_results"])
    assert report["production_claims"]["route_activation_effective"] is False
    assert report["production_claims"]["requested_window_bound"] is False
