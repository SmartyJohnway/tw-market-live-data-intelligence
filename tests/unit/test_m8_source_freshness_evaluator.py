import json
import re
from pathlib import Path

from scripts.m8_source_freshness_evaluator import (
    FRESHNESS_ASSESSMENT_SCHEMA_VERSION,
    build_source_freshness_assessment,
)

ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = ROOT / "docs/data_capabilities/m8_source_capability_registry.json"
INVENTORY_PATH = ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json"
PROFILE_PATH = ROOT / "config/test_execution_profiles.json"
MODULE_PATH = ROOT / "scripts/m8_source_freshness_evaluator.py"
DOC_PATH = ROOT / "docs/protocol/M8_SOURCE_FRESHNESS_EVALUATOR.md"


def _registry():
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _source(source_id):
    return next(source for source in _registry()["sources"] if source["source_id"] == source_id)


def test_pure_helper_has_no_network_or_runtime_imports():
    text = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_patterns = [
        r"^\s*import\s+requests\b",
        r"^\s*from\s+requests\b",
        r"^\s*import\s+httpx\b",
        r"^\s*from\s+httpx\b",
        r"urllib\.request",
        r"^\s*from\s+fastapi\b",
        r"^\s*import\s+fastapi\b",
        r"server\.main",
        r"^\s*import\s+frontend\b",
        r"^\s*from\s+frontend\b",
        r"^\s*import\s+openai\b",
        r"^\s*from\s+openai\b",
    ]
    assert not any(re.search(pattern, text, re.MULTILINE) for pattern in forbidden_patterns)


def test_twse_mis_fresh_intraday_snapshot_retrieved_time_only():
    result = build_source_freshness_assessment(
        {"retrieved_at_utc": "2026-07-10T01:00:00Z"},
        _source("TWSE_MIS"),
        now_utc="2026-07-10T01:05:00Z",
    )
    assert result["schema_version"] == FRESHNESS_ASSESSMENT_SCHEMA_VERSION
    assert result["freshness_assessment"] == "fresh_intraday_snapshot"
    assert result["intraday_snapshot"] is True
    assert result["age_seconds"] == 300
    assert result["exchange_timestamp_absent"] is True
    assert result["retrieved_time_only"] is True
    assert result["not_realtime_guaranteed"] is True
    assert result["not_trading_signal"] is True
    assert result["trading_advice_allowed"] is False


def test_twse_mis_stale_intraday_snapshot_not_current():
    result = build_source_freshness_assessment(
        {"retrieved_at_utc": "2026-07-10T00:00:00Z"},
        _source("TWSE_MIS"),
        now_utc="2026-07-10T01:00:01Z",
    )
    assert result["freshness_assessment"] == "stale_intraday_snapshot"
    assert result["stale_reason"]
    assert "stale source not safe to describe as current market" in result["blocked_interpretation"]
    assert result["requires_caveats"] is True


def test_future_retrieved_at_is_unknown_not_fresh():
    result = build_source_freshness_assessment(
        {"retrieved_at_utc": "2026-07-10T01:10:00Z"},
        _source("TWSE_MIS"),
        now_utc="2026-07-10T01:05:00Z",
    )
    assert result["freshness_assessment"] == "unknown"
    assert result["requires_caveats"] is True
    assert result["safe_for_ai_context"] is False
    assert result["not_realtime_guaranteed"] is True
    assert result["not_trading_signal"] is True
    assert any(
        "future retrieval timestamp" in caveat or "after now_utc" in caveat
        for caveat in result["caveats"]
    )


def test_twse_mis_unavailable_preserves_reason_and_is_not_context_safe():
    result = build_source_freshness_assessment(
        {"source_unavailable": True, "source_unavailable_reason": "network unavailable"},
        _source("TWSE_MIS"),
        now_utc="2026-07-10T01:05:00Z",
    )
    assert result["freshness_assessment"] == "source_unavailable"
    assert result["source_unavailable_reason"] == "network unavailable"
    assert result["safe_for_ai_context"] is False


def test_official_eod_sources_are_not_realtime_or_current_price():
    for source_id in ["TWSE_OPENAPI", "TPEX_OPENAPI"]:
        result = build_source_freshness_assessment({"market_date": "2026-07-09"}, _source(source_id))
        assert result["freshness_assessment"] == "official_eod_reference"
        assert result["eod_only"] is True
        assert result["not_realtime_guaranteed"] is True
        assert "not realtime" in result["blocked_interpretation"]
        assert "not current price" in result["blocked_interpretation"]
        assert result["trading_signal_allowed"] is False


def test_taifex_openapi_official_statistics_eod_is_not_live_signal():
    result = build_source_freshness_assessment({"market_date": "2026-07-09"}, _source("TAIFEX_OPENAPI"))
    assert result["freshness_assessment"] == "official_statistics_eod"
    assert result["not_realtime_guaranteed"] is True
    assert "not live derivatives signal" in result["blocked_interpretation"]
    assert "not leading indicator" in result["blocked_interpretation"]
    assert "not support/resistance" in result["blocked_interpretation"]
    assert result["trading_signal_allowed"] is False


def test_manual_operator_evidence_is_not_official_and_cannot_override():
    result = build_source_freshness_assessment({}, _source("MANUAL_OPERATOR_EVIDENCE"))
    assert result["freshness_assessment"] == "manual_snapshot"
    assert result["manual_snapshot"] is True
    assert "not official source" in result["blocked_interpretation"]
    assert "cannot override official source" in result["blocked_interpretation"]
    assert result["trading_signal_allowed"] is False


def test_external_validation_only_cannot_be_primary_context():
    result = build_source_freshness_assessment({}, _source("EXTERNAL_VALIDATION_ONLY"))
    assert result["freshness_assessment"] == "validation_only"
    assert result["validation_only"] is True
    assert "cannot be primary context" in result["blocked_interpretation"]
    assert result["safe_for_ai_context"] is False


def test_credential_gated_provider_metadata_only_no_network_or_credentials():
    result = build_source_freshness_assessment({}, _source("CREDENTIAL_GATED_PROVIDER"))
    assert result["freshness_assessment"] == "credential_gated_metadata_only"
    assert result["credential_gated"] is True
    assert "not runtime dependency" in result["blocked_interpretation"]
    assert result["safe_for_ai_context"] is False


def test_unknown_malformed_timestamp_does_not_raise_and_caveats():
    result = build_source_freshness_assessment(
        {"retrieved_at_utc": "not-a-timestamp"},
        _source("TWSE_MIS"),
        now_utc="2026-07-10T01:05:00Z",
    )
    assert result["freshness_assessment"] == "unknown"
    assert result["requires_caveats"] is True
    assert any("timestamp parse failure" in caveat for caveat in result["caveats"])


def test_registry_policies_remain_safe():
    sources = _registry()["sources"]
    ids = {source["source_id"] for source in sources}
    assert "TPEX_MIS" not in ids
    assert all("rotc_" not in json.dumps(source.get("market_scope", {})) for source in sources)
    for source_id in ["TWSE_OPENAPI", "TPEX_OPENAPI", "TAIFEX_OPENAPI", "TAIFEX_MIS"]:
        assert _source(source_id)["runtime_executable"] is False
    for source in sources:
        assert source["recommendation_allowed"] is False
        assert source["trading_signal_allowed"] is False
        assert source["raw_payload_exposure_allowed"] is False


def test_inventory_m8_00_04_metadata():
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    meta = inventory["rich_observation_contract"]["m8_source_timing_authority_governance"]
    assert meta["status"] in {"m8_00_source_freshness_evaluator_defined", "m8_00_multi_source_context_builder_defined", "m8_00_controlled_conversation_context_integration_and_compatibility_hardening_defined", "m8_00_final_acceptance_pass_with_caveats"}
    assert "M8-00-04" in meta["completed_tasks"]
    assert (ROOT / meta["source_freshness_evaluator_doc"]).exists()
    assert (ROOT / meta["source_freshness_evaluator_module"]).exists()
    assert meta["freshness_evaluator_added"] is True
    assert meta["freshness_evaluator_is_pure_helper"] is True
    assert meta["freshness_evaluator_network_access"] is False
    assert meta["runtime_behavior_changed"] is False
    assert meta["network_fetch_added"] is False
    assert meta["adapter_added"] is False
    assert meta["conversation_context_integration_added"] is False
    assert meta["next_task"] in {"M8-00-05-MULTI-SOURCE-CONTEXT-BUILDER", "M8-00-06-CONTROLLED-CONVERSATION-CONTEXT-INTEGRATION", "M8-00-08-FINAL-ACCEPTANCE-AND-CLOSURE", "M8A-00-OFFICIAL-EOD-ADAPTER-SCOPE-AND-CONTRACT-PREFLIGHT"}


def test_default_ci_includes_m8_00_04_test():
    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    assert "tests/unit/test_m8_source_freshness_evaluator.py" in profile["profiles"]["default-ci"]["pytest_paths"]
    assert DOC_PATH.exists()
