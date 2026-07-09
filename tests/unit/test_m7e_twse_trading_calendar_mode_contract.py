import json
from pathlib import Path

from scripts.twse_trading_calendar import build_twse_trading_calendar_authority_summary, build_twse_trading_calendar_from_holiday_schedule, resolve_twse_trading_day, load_twse_trading_calendar_artifact


def test_mode_abc_authority_summary():
    summary = build_twse_trading_calendar_authority_summary()
    assert summary["supported_modes"] == ["Mode A", "Mode B", "Mode C"]
    assert "shared resolver" in summary["mode_contract"]["mode_a"]
    assert "shared resolver" in summary["mode_contract"]["mode_b"]
    assert "shared resolver" in summary["mode_contract"]["mode_c"]
    assert summary["runtime_fetch"] is False
    assert summary["startup_network"] is False
    assert summary["not_full_exchange_calendar_engine"] is True
    assert summary["no_realtime_sla"] is True
    assert summary["not_trading_advice"] is True

def test_no_network_calls(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise AssertionError("network call attempted")
    import urllib.request
    monkeypatch.setattr(urllib.request, "urlopen", fail)
    try:
        import requests
        monkeypatch.setattr(requests, "get", fail)
    except Exception:
        pass
    try:
        import httpx
        monkeypatch.setattr(httpx, "get", fail)
    except Exception:
        pass
    cal = build_twse_trading_calendar_from_holiday_schedule(year=2026, holiday_schedule_records=[], generated_at_utc="2026-01-01T00:00:00Z")
    p = tmp_path / "cal.json"
    p.write_text(json.dumps(cal), encoding="utf-8")
    loaded = load_twse_trading_calendar_artifact(p)
    assert resolve_twse_trading_day(target_date="2026-01-05", calendar_artifact=loaded)["source"] == "local_calendar_artifact"

def test_inventory_registers_trading_calendar_authority():
    inv = json.loads(Path("docs/data_capabilities/twse_mis_rich_field_inventory.json").read_text(encoding="utf-8"))
    entry = inv["rich_observation_contract"]["m7e_twse_trading_calendar_authority"]
    assert entry["status"] == "shared_authority_defined"
    assert entry["runtime_network_fetch_added"] is False
    assert entry["startup_network_added"] is False
    assert entry["hidden_fetch_added"] is False
    assert entry["mode_a_supported"] is True
    assert entry["mode_b_supported"] is True
    assert entry["mode_c_supported"] is True
    assert entry["mode_abc_shared_authority"] is True
    assert entry["next_task"] == "M7F-FRONTEND-OPERATOR-PRESENTATION-AND-CONTEXT-WORKBENCH"
    m7e = inv["rich_observation_contract"]["m7e_market_clock_session_state"]
    assert m7e["trading_calendar_authority_added"] is True
    assert m7e["trading_calendar_authority"] == "m7e_twse_trading_calendar_authority"
