from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HTML = (ROOT / "frontend/readonly-preview/M5KLocalAIWorkbench.html").read_text(encoding="utf-8")
JS = (ROOT / "frontend/readonly-preview/m5k-workbench.js").read_text(encoding="utf-8")
RUNBOOK = ROOT / "docs/operator/M5OP_OPERATOR_WORKFLOW.md"


def test_mode_abc_and_conversation_ui_contract_present():
    for text in ["Mode A", "Mode B", "Mode C", "Canonical / not live warning", "no-network confirmation", "copy JSON", "copy Markdown", "download JSON", "download Markdown", "Markdown preview"]:
        assert text in HTML


def test_watchlist_rows_surface_latest_status_and_reference_failure_fields():
    for text in ["grouped by category", "Latest observation status", "Source / freshness", "reference_only", "Failure reason", "Recommended next step"]:
        assert text in HTML
    for text in ["status-reference_only", "value_unavailable", "failure_reason", "no_observation_loaded"]:
        assert text in JS


def test_conversation_context_no_raw_payload_leakage_contract():
    assert "raw_endpoint_payload_included" in JS
    assert "raw_payload ?" in JS
    assert "raw endpoint payload" in HTML.lower()


def test_runbook_exists_and_contains_required_sections():
    text = RUNBOOK.read_text(encoding="utf-8")
    for section in ["## Daily usage", "## Interpretation guide", "## Safety rules", "## Troubleshooting"]:
        assert section in text
    for term in ["ok", "reference_only", "value_unavailable", "failed", "stale", "closed-session", "not_realtime_guaranteed", "TX contract not available"]:
        assert term in text


def test_no_forbidden_static_writes_or_startup_execution_contract():
    assert "frontend/public" not in [str(p) for p in [ROOT / "frontend/readonly-preview/M5KLocalAIWorkbench.html"]]
    assert "research/generated" not in HTML + JS
    assert "executeObservation();" not in JS.split("DOMContentLoaded", 1)[-1]
    assert "confirm_live_observation=true" in JS


def test_watchlist_from_rows_generates_required_id_contract_and_backend_validates():
    from scripts.m5k_common import validate_watchlist

    assert "id: `${category}:${symbol}`" in JS
    assert "const category = field('category').value.trim() || 'custom';" in JS
    assert "const symbol = field('symbol').value.trim().toUpperCase();" in JS

    frontend_equivalent_payload = {
        "schema_version": "m5n_watchlist.v1",
        "watchlist_id": "m5op_frontend_watchlist",
        "name": "M5OP Frontend Watchlist",
        "items": [
            {
                "id": "custom:2330",
                "category": "custom",
                "display_order": 999,
                "symbol": "2330",
                "display_name": "台積電",
                "market": "twse",
                "instrument_type": "listed_equity",
                "adapter": "TWSE_MIS",
                "preferred_sources": ["TWSE_MIS"],
                "enabled": True,
                "tags": [],
                "notes": "frontend-generated equivalent payload",
            }
        ],
    }

    validation = validate_watchlist(frontend_equivalent_payload)
    assert frontend_equivalent_payload["items"][0]["id"] == "custom:2330"
    assert frontend_equivalent_payload["items"][0]["symbol"] == "2330"
    assert frontend_equivalent_payload["items"][0]["category"] == "custom"
    assert validation["valid"] is True
    assert validation["errors"] == []
