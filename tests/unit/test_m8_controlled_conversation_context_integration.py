import json
from pathlib import Path

from scripts.m8_controlled_conversation_context import CONTROLLED_CONVERSATION_CONTEXT_SCHEMA_VERSION, M8_CONVERSATION_SECTION_ID, build_controlled_conversation_context
from scripts.m8_multi_source_context_builder import build_multi_source_market_context

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = json.loads((ROOT / "docs/data_capabilities/m8_source_capability_registry.json").read_text())


def _obs(source_id="TWSE_MIS", **kw):
    base = {"source_id": source_id, "symbol": "2330", "name": "TSMC", "market": "listed", "instrument_type": "equity", "context_type": "fixture", "retrieved_at_utc": "2026-07-10T01:00:00Z", "safe_fields": {"price_like_value": 2415}}
    base.update(kw)
    return base


def _projection(observations, now="2026-07-10T01:05:00Z"):
    return build_controlled_conversation_context(build_multi_source_market_context(observations, REGISTRY, now_utc=now))


def _contexts(proj):
    return [ctx for inst in proj["sections"][0]["instrument_contexts"] for ctx in inst["contexts"]]


def test_pure_projection_no_network_runtime_imports():
    text = (ROOT / "scripts/m8_controlled_conversation_context.py").read_text().lower()
    for forbidden in ["import requests", "import httpx", "urllib.request", "fastapi", "server.main", "frontend", "openai", "import mcp", "from mcp"]:
        assert forbidden not in text


def test_ready_with_caveats_for_mixed_twse_mis_twse_openapi():
    proj = _projection([_obs(), _obs("TWSE_OPENAPI", market_date="2026-07-09", safe_fields={"close": 2, "trade_date": "2026-07-09"})])
    section = proj["sections"][0]
    assert proj["schema_version"] == CONTROLLED_CONVERSATION_CONTEXT_SCHEMA_VERSION
    assert proj["context_status"] == "ready_with_caveats"
    assert section["section_id"] == M8_CONVERSATION_SECTION_ID
    assert any(c["source_id"] == "TWSE_MIS" and c["safe_fields"].get("price_like_value") == 2415 for c in _contexts(proj))
    assert any(c["source_id"] == "TWSE_OPENAPI" and c["safe_fields"].get("close") == 2 for c in _contexts(proj))
    assert "EOD" in " ".join(section["caveats"])
    assert "not trading advice" in section["markdown"] and "not a recommendation" in section["markdown"] and "not a trading signal" in section["markdown"]
    assert "raw_payload" not in section["markdown"]


def test_metadata_only_projection_for_unknown_only_source():
    proj = _projection([_obs("UNKNOWN_VENDOR", safe_fields={"price_like_value": 123})])
    assert proj["context_status"] in {"metadata_only", "blocked"}
    ctx = _contexts(proj)[0]
    assert ctx["source_id"] == "UNKNOWN_VENDOR"
    assert "price_like_value" not in ctx["safe_fields"]
    assert "unknown source safe_fields withheld from conversation context" in " ".join(ctx["caveats"] + proj["sections"][0]["caveats"])


def test_stale_source_projection():
    proj = _projection([_obs(retrieved_at_utc="2026-07-10T00:00:00Z")])
    ctx = _contexts(proj)[0]
    assert ctx["primary_context_allowed"] is False
    assert "stale source must not be described as current market" in " ".join(ctx["caveats"])
    assert "current market" not in proj["sections"][0]["markdown"].replace("must not be described as current market", "")


def test_validation_only_projection():
    proj = _projection([_obs("EXTERNAL_VALIDATION_ONLY")])
    ctx = _contexts(proj)[0]
    assert ctx["supporting_context_only"] is True
    assert ctx["primary_context_allowed"] is False
    assert "validation-only source cannot be primary context" in " ".join(ctx["caveats"])
    assert proj["not_trading_signal"] is True


def test_manual_evidence_projection():
    proj = _projection([_obs("TWSE_OPENAPI", market_date="2026-07-09", safe_fields={"close": 2}), _obs("MANUAL_OPERATOR_EVIDENCE", safe_fields={"operator_note": "screen observed"})])
    manual = [c for c in _contexts(proj) if c["source_id"] == "MANUAL_OPERATOR_EVIDENCE"][0]
    assert manual["primary_context_allowed"] is False
    assert "manual evidence is not official source" in " ".join(manual["caveats"])


def test_credential_gated_projection():
    proj = _projection([_obs("CREDENTIAL_GATED_PROVIDER", safe_fields={"provider_name": "fixture", "secret": "no"})])
    ctx = _contexts(proj)[0]
    assert ctx["metadata_only"] is True
    text = json.dumps(proj).lower()
    assert "secret" not in ctx["safe_fields"]
    assert "not runtime dependency" in text


def test_forbidden_raw_fields_blocked_from_projection_and_markdown():
    proj = _projection([_obs(safe_fields={"price_like_value": 2415, "raw_payload": {}, "bid_prices": [1], "ask_prices": [2], "source_investigation_notes": "raw"})])
    ctx = _contexts(proj)[0]
    assert ctx["safe_fields"].get("price_like_value") == 2415
    for key in ["raw_payload", "bid_prices", "ask_prices", "source_investigation_notes"]:
        assert key not in ctx["safe_fields"]
        assert key not in proj["sections"][0]["markdown"]
    assert proj["no_raw_payload"] is True


def test_wrong_schema_is_blocked():
    proj = build_controlled_conversation_context({"schema_version": "wrong"})
    assert proj["context_status"] == "blocked"
    assert proj["sections"][0]["instrument_contexts"] == []
    assert "wrong schema" in " ".join(proj["sections"][0]["caveats"])


def test_default_ci_includes_new_test():
    config = json.loads((ROOT / "config/test_execution_profiles.json").read_text())
    assert "tests/unit/test_m8_controlled_conversation_context_integration.py" in config["profiles"]["default-ci"]["pytest_paths"]
