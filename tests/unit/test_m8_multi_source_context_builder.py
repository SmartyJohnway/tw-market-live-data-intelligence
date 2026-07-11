import json
from pathlib import Path

from scripts.m8_multi_source_context_builder import (
    MULTI_SOURCE_CONTEXT_SCHEMA_VERSION,
    build_multi_source_market_context,
)

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = json.loads((ROOT / "docs/data_capabilities/m8_source_capability_registry.json").read_text())


def _ctx(result, source_id):
    for inst in result["instrument_contexts"]:
        for ctx in inst["contexts"]:
            if ctx["source_id"] == source_id:
                return ctx
    raise AssertionError(source_id)


def _obs(source_id="TWSE_MIS", **kw):
    base = {"source_id": source_id, "symbol": "2330", "name": "TSMC", "market": "listed", "instrument_type": "equity", "context_type": "fixture", "retrieved_at_utc": "2026-07-10T01:00:00Z", "safe_fields": {"price_like_value": 2415}}
    base.update(kw)
    return base


def test_pure_helper_has_no_network_or_runtime_imports():
    text = (ROOT / "scripts/m8_multi_source_context_builder.py").read_text().lower()
    for forbidden in ["import requests", "import httpx", "urllib.request", "fastapi", "server.main", "frontend", "openai", "import mcp", "from mcp"]:
        assert forbidden not in text


def test_empty_context():
    result = build_multi_source_market_context([], REGISTRY, now_utc="2026-07-10T01:05:00Z")
    assert result["schema_version"] == MULTI_SOURCE_CONTEXT_SCHEMA_VERSION
    assert result["context_status"] == "empty_context"
    assert result["instrument_contexts"] == []
    assert result["not_trading_signal"] is True
    assert result["not_recommendation"] is True


def test_twse_mis_fresh_liveish_observation():
    result = build_multi_source_market_context([_obs(context_type="liveish_quote_observation")], REGISTRY, now_utc="2026-07-10T01:05:00Z")
    ctx = _ctx(result, "TWSE_MIS")
    assert result["freshness_summary"]["has_liveish_intraday_snapshot"] is True
    assert ctx["freshness_assessment"] == "fresh_intraday_snapshot"
    assert result["context_status"] in {"candidate_built", "candidate_built_with_caveats"}
    assert ctx["safe_fields"]["price_like_value"] == 2415
    assert ctx["not_trading_signal"] is True
    assert result["ai_exposure_policy"]["not_recommendation"] is True


def test_twse_mis_stale_observation_included_but_caveated():
    result = build_multi_source_market_context([_obs(retrieved_at_utc="2026-07-10T00:00:00Z")], REGISTRY, now_utc="2026-07-10T01:05:00Z")
    ctx = _ctx(result, "TWSE_MIS")
    assert ctx["freshness_assessment"] == "stale_intraday_snapshot"
    assert result["freshness_summary"]["has_stale_sources"] is True
    assert result["instrument_contexts"]
    assert ctx["primary_context_allowed"] is False
    assert "stale source must not be described as current market" in " ".join(ctx["caveats"] + result["cross_source_caveats"])


def test_mixed_twse_mis_and_twse_openapi_same_symbol():
    eod = _obs("TWSE_OPENAPI", context_type="official_eod_reference", safe_fields={"trade_date": "2026-07-09", "open": 1, "high": 2, "low": 1, "close": 2, "trade_volume": 100})
    result = build_multi_source_market_context([_obs(context_type="liveish_quote_observation"), eod], REGISTRY, now_utc="2026-07-10T01:05:00Z")
    assert len(result["instrument_contexts"]) == 1
    ids = {c["source_id"] for c in result["instrument_contexts"][0]["contexts"]}
    assert ids == {"TWSE_MIS", "TWSE_OPENAPI"}
    assert result["freshness_summary"]["has_liveish_intraday_snapshot"] is True
    assert result["freshness_summary"]["has_official_eod_reference"] is True
    assert result["freshness_summary"]["caveated_currentness_label"] == "mixed_liveish_and_eod_context"
    assert _ctx(result, "TWSE_MIS")["safe_fields"] == {"price_like_value": 2415}
    assert "EOD source must not be described as realtime" in result["cross_source_caveats"]
    assert result["ai_exposure_policy"]["safe_to_include_in_conversation_context"] is True
    assert result["ai_exposure_policy"]["requires_caveats"] is True


def test_tpex_openapi_official_eod_reference_no_tpex_mis():
    obs = _obs("TPEX_OPENAPI", symbol="8069", market="tpex_otc", safe_fields={"close": 100, "trade_date": "2026-07-09"})
    result = build_multi_source_market_context([obs], REGISTRY, now_utc="2026-07-10T01:05:00Z")
    assert _ctx(result, "TPEX_OPENAPI")["freshness_assessment"] == "official_eod_reference"
    assert "EOD source must not be described as realtime" in result["cross_source_caveats"]
    assert all(s["source_id"] != "TPEX_MIS" for s in result["sources"])


def test_taifex_openapi_official_statistics_eod():
    obs = _obs("TAIFEX_OPENAPI", symbol="TXO", market="derivatives", instrument_type="derivative_statistic", context_type="official_derivatives_statistics_eod", safe_fields={"put_call_ratio": 1.1})
    result = build_multi_source_market_context([obs], REGISTRY, now_utc="2026-07-10T01:05:00Z")
    assert _ctx(result, "TAIFEX_OPENAPI")["freshness_assessment"] == "official_statistics_eod"
    caveats = " ".join(result["cross_source_caveats"] + _ctx(result, "TAIFEX_OPENAPI")["caveats"])
    assert "not be described as live derivatives signal" in caveats
    assert "leading indicator" in caveats
    assert "support/resistance" in result["ai_exposure_policy"]["forbidden_interpretations"]


def test_manual_evidence_with_official_source():
    off = _obs("TWSE_OPENAPI", safe_fields={"close": 2, "trade_date": "2026-07-09"})
    manual = _obs("MANUAL_OPERATOR_EVIDENCE", safe_fields={"operator_note": "screen observed"})
    result = build_multi_source_market_context([off, manual], REGISTRY, now_utc="2026-07-10T01:05:00Z")
    manual_ctx = _ctx(result, "MANUAL_OPERATOR_EVIDENCE")
    assert manual_ctx["primary_context_allowed"] is False
    assert "manual evidence cannot override official source" in " ".join(manual_ctx["caveats"] + result["cross_source_caveats"])


def test_external_validation_only_supporting():
    result = build_multi_source_market_context([_obs("EXTERNAL_VALIDATION_ONLY")], REGISTRY, now_utc="2026-07-10T01:05:00Z")
    ctx = _ctx(result, "EXTERNAL_VALIDATION_ONLY")
    assert ctx["supporting_context_only"] is True
    assert ctx["primary_context_allowed"] is False
    assert "validation-only source cannot be primary context" in " ".join(ctx["caveats"] + result["cross_source_caveats"])


def test_credential_gated_provider_metadata_only():
    result = build_multi_source_market_context([_obs("CREDENTIAL_GATED_PROVIDER", safe_fields={"provider_name": "fixture"})], REGISTRY, now_utc="2026-07-10T01:05:00Z")
    ctx = _ctx(result, "CREDENTIAL_GATED_PROVIDER")
    assert ctx["metadata_only"] is True
    assert ctx["primary_context_allowed"] is False
    assert "not runtime dependency" in " ".join(ctx["caveats"] + result["cross_source_caveats"])


def test_unknown_source_id():
    result = build_multi_source_market_context([_obs("UNKNOWN_VENDOR")], REGISTRY, now_utc="2026-07-10T01:05:00Z")
    ctx = _ctx(result, "UNKNOWN_VENDOR")
    assert result["context_status"] in {"candidate_built_with_caveats", "empty_context"}
    assert result["freshness_summary"]["has_unknown_sources"] is True
    assert ctx["primary_context_allowed"] is False
    assert "unknown source_id" in " ".join(result["cross_source_caveats"])
    assert result["ai_exposure_policy"]["safe_to_include_in_conversation_context"] is False


def test_raw_field_scrubbing():
    result = build_multi_source_market_context([_obs(safe_fields={"price_like_value": 2415, "raw_payload": {}, "bid_prices": [1], "ask_prices": [2], "source_investigation_notes": "raw"})], REGISTRY, now_utc="2026-07-10T01:05:00Z")
    ctx = _ctx(result, "TWSE_MIS")
    assert ctx["safe_fields"] == {"price_like_value": 2415}
    assert {"raw_payload", "bid_prices", "ask_prices", "source_investigation_notes"}.issubset(set(ctx["omitted_fields"]))
    assert "forbidden raw fields were omitted from safe_fields" in result["cross_source_caveats"]
    assert "raw_payload" in result["ai_exposure_policy"]["blocked_fields"]


def test_inventory_m8_00_05_metadata():
    inv = json.loads((ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json").read_text())
    entry = inv["rich_observation_contract"]["m8_source_timing_authority_governance"]
    assert entry["status"] == "m8_00_multi_source_context_builder_defined"
    assert "M8-00-05" in entry["completed_tasks"]
    assert (ROOT / entry["multi_source_context_builder_doc"]).exists()
    assert (ROOT / entry["multi_source_context_builder_module"]).exists()
    assert entry["multi_source_context_builder_added"] is True
    assert entry["multi_source_context_builder_is_pure_helper"] is True
    assert entry["multi_source_context_builder_network_access"] is False
    assert entry["runtime_behavior_changed"] is False
    assert entry["adapter_added"] is False
    assert entry["conversation_context_integration_added"] is False
    assert entry["next_task"] == "M8-00-06-CONTROLLED-CONVERSATION-CONTEXT-INTEGRATION"


def test_default_ci_includes_builder_test():
    config = json.loads((ROOT / "config/test_execution_profiles.json").read_text())
    assert "tests/unit/test_m8_multi_source_context_builder.py" in config["profiles"]["default-ci"]["pytest_paths"]
