from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from scripts import m5q_source_health as m5q
from scripts.observation_contract import normalize_observation
from server.main import app


def test_check_only_does_not_write_or_call_network(monkeypatch, tmp_path):
    monkeypatch.setattr(m5q, "SOURCE_HEALTH_DIR", tmp_path)
    monkeypatch.setattr(m5q, "REPORT_JSON", tmp_path / "source_health_report.json")
    monkeypatch.setattr(m5q, "LATEST_JSON", tmp_path / "latest_source_health_report.json")
    def boom(*a, **k):
        raise AssertionError("network execution must not happen")
    monkeypatch.setattr(m5q, "execute_live_observation", boom)
    report = m5q.build_report(execution_mode="check_only")
    assert report["network_calls_may_have_occurred"] is False
    assert report["bounded"] is True
    assert report["full_market_scan"] is False
    assert not list(tmp_path.iterdir())


def test_health_targets_are_bounded_and_schema_has_no_raw_payload():
    report = m5q.build_report(execution_mode="check_only")
    assert report["schema_version"] == "m5q_source_health_report.v1"
    assert report["targets"] == ["2330", "0050", "3483", "TAIEX", "TX"]
    assert len(report["checks"]) == 5
    assert all(c["raw_endpoint_payload_included"] is False for c in report["checks"])
    assert "raw_payload" not in json.dumps(report)


def test_health_classification_cases():
    ok = normalize_observation(symbol="2330", source="TWSE_MIS", adapter_id="twse", status="ok", retrieved_at_utc="2026-06-30T00:00:00Z", value=1.0, reference_only=False, freshness_assessment="fresh")
    ref = ok | {"status": "reference_value_only", "reference_only": True}
    stale = ok | {"freshness_assessment": "stale_or_closed_session"}
    assert m5q.classify_observation(ok) == "healthy"
    assert m5q.classify_observation(ref) == "degraded"
    assert m5q.classify_observation(stale) == "degraded"
    assert m5q.classify_observation(None, {"status": "failed", "reason": "malformed"}) == "failed"
    assert m5q.classify_observation(None, {"status": "unsupported", "reason": "unsupported_route"}) == "unsupported"


def test_reference_failure_embedded_observation_preserves_detail():
    embedded = normalize_observation(
        symbol="2330",
        source="TWSE_MIS",
        adapter_id="twse_mis_equity_etf_quote",
        status="reference_value_only",
        retrieved_at_utc="2026-06-30T01:02:03Z",
        value=123.5,
        reference_only=True,
        source_timestamp="2026-06-30T01:01:30Z",
        freshness_assessment="current observation candidate; realtime status not guaranteed by M5K",
        delay_seconds=33,
        caveats=["current_z_unavailable_y_reference_fallback_not_current_trade"],
    )
    failure = {
        "symbol": "2330",
        "source": "TWSE_MIS",
        "adapter_id": "twse_mis_equity_etf_quote",
        "reason": "reference_value_only",
        "investigation_summary": {"observation": embedded},
        "caveats": ["not_realtime_guaranteed"],
    }
    plan = {
        "symbol": "2330",
        "instrument_type": "listed_equity",
        "market": "twse",
        "source": "TWSE_MIS",
        "adapter_id": "twse_mis_equity_etf_quote",
        "ex_ch": "tse_2330.tw",
        "status": "planned",
    }
    check = m5q._check_from_plan(plan, None, failure, "2026-06-30T01:02:04Z")
    assert check["status"] == "degraded"
    assert check["observation_status"] == "reference_value_only"
    assert check["reference_only"] is True
    assert check["value_present"] is True
    assert check["source_timestamp"] == "2026-06-30T01:01:30Z"
    assert check["delay_seconds"] == 33
    assert check["freshness_assessment"] == "current observation candidate; realtime status not guaranteed by M5K"
    assert "current_z_unavailable_y_reference_fallback_not_current_trade" in check["caveats"]
    assert check["failure_reason"] == "reference_value_only"


def test_read_latest_source_health_unavailable_and_available(monkeypatch, tmp_path):
    path = tmp_path / "latest_source_health_report.json"
    monkeypatch.setattr(m5q, "LATEST_JSON", path)
    assert m5q.read_latest_source_health()["status"] == "not_available"
    path.write_text(json.dumps({"schema_version": m5q.SCHEMA_VERSION, "summary": {}}), encoding="utf-8")
    got = m5q.read_latest_source_health()
    assert got["status"] == "ok"
    assert got["content"]["schema_version"] == m5q.SCHEMA_VERSION


def test_fastapi_source_health_endpoints(monkeypatch, tmp_path):
    path = tmp_path / "latest_source_health_report.json"
    import server.main as main
    def fake_missing():
        return {"status": "not_available"}
    monkeypatch.setattr(main, "_m5q_read_latest_source_health", fake_missing)
    client = TestClient(app)
    assert client.get("/api/source-health/latest").json()["status"] == "not_available"
    def fake_available():
        return {"status": "ok", "content": {"schema_version": m5q.SCHEMA_VERSION, "summary": {"healthy": 1}, "checks": []}}
    monkeypatch.setattr(main, "_m5q_read_latest_source_health", fake_available)
    assert client.get("/api/source-health/latest").json()["status"] == "ok"
    assert client.get("/api/source-health/schema").json()["content"]["schema_version"] == m5q.SCHEMA_VERSION


def test_conversation_source_health_available_unavailable(monkeypatch, tmp_path):
    from scripts.m5k_common import build_conversation_context
    path = tmp_path / "latest_source_health_report.json"
    monkeypatch.setattr(m5q, "LATEST_JSON", path)
    wl = m5q.selected_health_watchlist()
    assert build_conversation_context(wl, {})["source_health"]["source_health_status"] == "not_available"
    path.write_text(json.dumps({"schema_version": m5q.SCHEMA_VERSION, "generated_at_utc": "x", "summary": {"failed": 1}, "checks": [{"target":"2330", "source_family":"TWSE_MIS listed stock route", "status":"failed", "observation_status":"failed", "freshness_assessment":"failed"}], "caveats": ["c"]}), encoding="utf-8")
    health = build_conversation_context(wl, {})["source_health"]
    assert health["source_health_status"] == "available"
    assert health["raw_endpoint_payload_included"] is False


def test_frontend_source_health_panel_static_contract():
    html = Path("frontend/readonly-preview/M5KLocalAIWorkbench.html").read_text(encoding="utf-8")
    js = Path("frontend/readonly-preview/m5k-workbench.js").read_text(encoding="utf-8")
    assert "Source Health Panel" in html
    assert "/api/source-health/latest" in js
    assert "loadSourceHealth" in js
