import json
from pathlib import Path

from scripts.m8_controlled_conversation_context import build_controlled_conversation_context
from scripts.m8_multi_source_context_builder import build_multi_source_market_context

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = json.loads((ROOT / "docs/data_capabilities/m8_source_capability_registry.json").read_text())


def _obs(source_id="TWSE_MIS", **kw):
    base = {"source_id": source_id, "symbol": "2330", "name": "TSMC", "market": "listed", "instrument_type": "equity", "context_type": "fixture", "retrieved_at_utc": "2026-07-10T01:00:00Z", "safe_fields": {"price_like_value": 2415}}
    base.update(kw)
    return base


def _proj(obs, now="2026-07-10T01:05:00Z"):
    return build_controlled_conversation_context(build_multi_source_market_context(obs, REGISTRY, now_utc=now))


def _ctxs(proj):
    return [ctx for inst in proj["sections"][0]["instrument_contexts"] for ctx in inst["contexts"]]


def test_eod_not_projected_as_realtime():
    proj = _proj([_obs("TWSE_OPENAPI", market_date="2026-07-09", safe_fields={"close": 1}), _obs("TPEX_OPENAPI", symbol="8069", market="tpex_otc", market_date="2026-07-09", safe_fields={"close": 2})])
    text = json.dumps(proj).lower()
    assert "eod" in text or "reference" in text
    assert "not realtime" in text
    assert "current price" not in text.replace("not current price", "").replace("must not be described as current price", "").replace("not be described as realtime or current price", "")


def test_retrieved_at_utc_not_projected_as_exchange_timestamp():
    proj = _proj([_obs()])
    markdown = proj["sections"][0]["markdown"].lower()
    assert "retrieved_at_utc is not exchange timestamp" in json.dumps(proj).lower()
    assert "exchange timestamp" not in markdown.replace("retrieved_at_utc is not exchange timestamp unless source_timestamp proves it", "").replace("retrieved_at_utc is not exchange timestamp", "")


def test_stale_not_current():
    proj = _proj([_obs(retrieved_at_utc="2026-07-10T00:00:00Z")])
    text = json.dumps(proj).lower()
    assert "stale source must not be described as current market" in text
    assert "current market" not in text.replace("stale source must not be described as current market", "")


def test_manual_not_official():
    proj = _proj([_obs("MANUAL_OPERATOR_EVIDENCE", safe_fields={"operator_note": "screen"})])
    manual = _ctxs(proj)[0]
    assert "manual evidence is not official source" in " ".join(manual["caveats"])
    assert manual["authority_level"] != "official_documented"


def test_validation_only_not_primary():
    ctx = _ctxs(_proj([_obs("EXTERNAL_VALIDATION_ONLY")]))[0]
    assert ctx["primary_context_allowed"] is False
    assert ctx["supporting_context_only"] is True


def test_credential_gated_not_runtime_dependency():
    proj = _proj([_obs("CREDENTIAL_GATED_PROVIDER", safe_fields={"provider_name": "fixture", "credential": "x"})])
    ctx = _ctxs(proj)[0]
    assert ctx["metadata_only"] is True
    assert "credential" not in ctx["safe_fields"]
    assert "not runtime dependency" in json.dumps(proj).lower()


def test_unknown_source_safe_fields_withheld():
    proj = _proj([_obs("UNKNOWN_VENDOR", safe_fields={"price_like_value": 9})])
    ctx = _ctxs(proj)[0]
    assert ctx["safe_fields"] == {}
    assert "unknown source safe_fields withheld" in json.dumps(proj)


def test_forbidden_raw_fields_absent_from_markdown_and_safe_fields():
    proj = _proj([_obs(safe_fields={"price_like_value": 1, "raw_payload": {}, "bid_prices": [], "ask_prices": [], "bid_volumes": [], "ask_volumes": [], "raw_bid_ask_ladder": [], "order_book_truth": True, "source_investigation_notes": "x"})])
    markdown = proj["sections"][0]["markdown"]
    for ctx in _ctxs(proj):
        for key in ["raw_payload", "bid_prices", "ask_prices", "bid_volumes", "ask_volumes", "raw_bid_ask_ladder", "order_book_truth", "source_investigation_notes"]:
            assert key not in ctx["safe_fields"]
            assert key not in markdown


def test_no_trading_advice_signal_recommendation():
    proj = _proj([_obs()])
    text = proj["sections"][0]["markdown"].lower()
    for term in ["buy", "sell", "hold", "bullish", "bearish", "target price", "ranking", "top movers", "strongest", "weakest"]:
        assert term not in text
    assert "support/resistance" not in text
    assert proj["no_trading_advice"] is True and proj["not_recommendation"] is True and proj["not_trading_signal"] is True


def test_source_taxonomy_remains_clean():
    inv = json.loads((ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json").read_text())
    entry = inv["rich_observation_contract"]["m8_source_timing_authority_governance"]
    assert entry.get("tpex_mis_introduced") is False
    assert entry.get("rotc_route_introduced") is False
    assert entry.get("taifex_mis_execution_added") is False
    assert entry.get("twse_openapi_adapter_added") is False


def test_inventory_m8_00_06_07_metadata():
    inv = json.loads((ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json").read_text())
    entry = inv["rich_observation_contract"]["m8_source_timing_authority_governance"]
    assert entry["status"] == "m8_00_controlled_conversation_context_integration_and_compatibility_hardening_defined"
    assert "M8-00-06" in entry["completed_tasks"] and "M8-00-07" in entry["completed_tasks"]
    assert (ROOT / entry["controlled_conversation_context_doc"]).exists()
    assert (ROOT / entry["controlled_conversation_context_module"]).exists()
    assert (ROOT / entry["compatibility_hardening_doc"]).exists()
    assert entry["network_fetch_added"] is False and entry["server_changed"] is False and entry["frontend_changed"] is False and entry["mcp_changed"] is False and entry["adapter_added"] is False
    assert entry["m8_00_05_caveats_fixed"] is True
    assert entry["next_task"] == "M8-00-08-FINAL-ACCEPTANCE-AND-CLOSURE"


def test_default_ci_includes_hardening_test():
    config = json.loads((ROOT / "config/test_execution_profiles.json").read_text())
    assert "tests/unit/test_m8_compatibility_hardening.py" in config["profiles"]["default-ci"]["pytest_paths"]
