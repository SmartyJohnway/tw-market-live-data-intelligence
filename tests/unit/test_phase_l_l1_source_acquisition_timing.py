from __future__ import annotations

import json
from pathlib import Path

from scripts import m8r_06_03_production_adapter as production
from server import operational_diagnostics as ops
from server.services import phase_i_i1_production_candidate as i1

ROOT = Path(__file__).resolve().parents[2]


def test_i1_source_timing_event_reuses_trace_and_excludes_raw_url(tmp_path, monkeypatch):
    sink = tmp_path / "operational-events.jsonl"
    monkeypatch.setenv(ops.EVENT_PATH_ENV, str(sink))
    trace = "12345678-1234-5678-1234-567812345678"
    bound, token = ops.bind_trace_id(trace)
    assert bound == trace
    source_id = "I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI"
    source_url = i1.SOURCE_DESCRIPTORS[source_id]["url"]
    monkeypatch.setattr(
        i1,
        "_http_transport",
        lambda _url, _timeout: (200, {"Content-Type": "application/json"}, b"[]"),
    )
    try:
        result = production._phase_i_i1_timed_transport(source_url, i1.TIMEOUT_SECONDS)
    finally:
        ops.reset_trace_id(token)

    assert result == (200, {"Content-Type": "application/json"}, b"[]")
    lines = sink.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    event = json.loads(lines[0])
    assert event["event_code"] == "source.acquisition.completed"
    assert event["trace_id"] == trace
    assert event["source_id"] == "I1-TPEX-MAINBOARD-HIGHLIGHT-OPENAPI"
    assert event["market"] == "TPEX"
    assert event["capability_id"] == "market_state_context"
    assert event["status"] == "returned"
    assert event["metrics"]["duration_ms"] >= 0
    assert i1.SOURCE_DESCRIPTORS[event["source_id"]]["url"] not in lines[0]


def test_current_production_source_modules_keep_timing_seams():
    expected = {
        "scripts/m8r_06_03_production_adapter.py": 8,
        "server/services/phase_h_h1_tpex_composite.py": 1,
        "server/services/phase_h_h2_twse_exright_executor.py": 1,
        "server/services/phase_i_i2_production_transport.py": 1,
        "server/services/phase_i_i3_cash_institutional_flow_production_candidate.py": 1,
    }

    for relative_path, minimum_calls in expected.items():
        text = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "from server.operational_diagnostics import timed_source_call" in text
        assert text.count("timed_source_call(") >= minimum_calls


def test_source_id_is_allowlisted_but_raw_url_is_not():
    event = ops.build_event(
        component="source_transport",
        event_code="source.acquisition.completed",
        status="returned",
        references={
            "source_id": "SOURCE-1",
            "market": "TWSE",
            "capability_id": "recent_performance",
            "url": "https://example.invalid/secret",
        },
        metrics={"duration_ms": 1.25},
    )
    encoded = ops.serialize_event(event)
    assert event["source_id"] == "SOURCE-1"
    assert "https://" not in encoded
    assert '"url"' not in encoded
