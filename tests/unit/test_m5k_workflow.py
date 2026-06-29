import json
from pathlib import Path
from fastapi.testclient import TestClient

from server.main import app
from scripts.m5k_common import conversation_handoff_from_watchlist, execute_live_observation, load_json, validate_watchlist

client = TestClient(app)
DEFAULT = Path("config/m5k_default_watchlist.json")


def test_default_watchlist_contains_required_symbols_and_validates():
    watchlist = load_json(DEFAULT)
    result = validate_watchlist(watchlist)
    assert result["valid"] is True
    for symbol in ["00878", "00919", "00929", "00934", "00939", "00940", "00981A", "1569", "2324", "2603", "2609", "3293", "3483", "3543", "2317", "2330", "0050", "TAIEX", "TX"]:
        assert symbol in result["symbols"]


def test_watchlist_validation_rejects_trading_signal_fields():
    watchlist = load_json(DEFAULT)
    watchlist["categories"][0]["instruments"][0]["recommendation"] = "buy"
    result = validate_watchlist(watchlist)
    assert result["valid"] is False
    assert any("forbidden_field" in e for e in result["errors"])


def test_conversation_handoff_is_machine_readable():
    handoff = conversation_handoff_from_watchlist(load_json(DEFAULT))
    assert handoff["schema_version"] == "m5k_conversation_handoff.v1"
    assert handoff["validation"]["valid"] is True
    assert "execute_bounded_live_observation" in handoff["frontend_actions"]
    assert handoff["governance"]["canonical"] is False


def test_live_observation_invalid_watchlist_fails_closed_without_network():
    result = execute_live_observation({"schema_version": "m5k_watchlist.v1", "categories": []}, write_latest=False)
    assert result["status"] == "failed_closed_invalid_watchlist"
    assert result["governance"]["promote_to_m5f"] is False


def test_fastapi_m5k_endpoints_are_offline_until_execute_confirmation():
    r = client.get("/api/m5k/watchlist/default")
    assert r.status_code == 200
    assert r.json()["validation"]["valid"] is True
    no_confirm = client.post("/api/m5k/live-observation/execute", json=r.json()["content"])
    assert no_confirm.status_code == 400
    handoff = client.post("/api/m5k/conversation/handoff", json=r.json()["content"])
    assert handoff.status_code == 200
    assert handoff.json()["schema_version"] == "m5k_conversation_handoff.v1"


def test_frontend_model_uses_m5k_endpoints_not_public_publication():
    html = Path("frontend/readonly-preview/M5KLocalAIWorkbench.html").read_text(encoding="utf-8")
    js = Path("frontend/readonly-preview/m5k-workbench.js").read_text(encoding="utf-8")
    assert "/api/m5k/watchlist/default" in js
    assert "confirm_live_observation=true" in js
    assert "frontend/public" not in html + js
