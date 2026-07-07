import json

import pytest

from scripts.m5k_common import (
    build_conversation_context,
    build_watchlist_rows,
    read_latest_observation,
    source_capabilities,
)
from scripts.m5q_source_health import build_report, classify_observation
from scripts.observation_contract import (
    build_empty_twse_mis_rich_facts,
    normalize_failure,
    normalize_observation,
    normalize_taifex_row,
    normalize_twse_mis_row,
)


RETRIEVED_AT = "2026-07-07T04:00:00Z"


def _watchlist():
    return {
        "schema_version": "m5n_watchlist.v1",
        "watchlist_id": "m7a_compat",
        "name": "M7A compatibility",
        "items": [
            {
                "id": "twse:2330",
                "symbol": "2330",
                "display_name": "TSMC",
                "market": "twse",
                "instrument_type": "listed_stock",
                "adapter": "twse_mis_equity_etf_quote",
                "category": "equity",
                "enabled": True,
                "display_order": 1,
                "tags": [],
                "notes": "",
            }
        ],
    }


def _twse_row(**overrides):
    row = {
        "c": "2330",
        "ch": "2330.tw",
        "ex": "tse",
        "n": "台積電",
        "nf": "台灣積體電路製造股份有限公司",
        "z": "1000.00",
        "y": "995.00",
        "o": "996.00",
        "h": "1005.00",
        "l": "990.00",
        "v": "12",
        "tv": "3456",
        "b": "999.00_998.00",
        "g": "10_20",
        "a": "1000.00_1001.00",
        "f": "11_21",
        "u": "1094.00",
        "w": "896.00",
        "d": "20260707",
        "t": "12:00:00",
        "tlong": "1783425600000",
        "ts": "0",
        "pz": "1000.00",
        "ps": "12",
    }
    row.update(overrides)
    return row


def _rich_observation(**row_overrides):
    return normalize_twse_mis_row(
        _twse_row(**row_overrides),
        {
            "symbol": "2330",
            "display_symbol": "2330",
            "market": "twse",
            "instrument_type": "listed_stock",
            "adapter_id": "twse_mis_equity_etf_quote",
        },
        RETRIEVED_AT,
        caveats=["not_realtime_guaranteed", "no_trading_signal"],
    )


def test_latest_observation_payload_with_rich_facts_is_read_without_shape_change(tmp_path, monkeypatch):
    latest = {
        "schema_version": "m5k_live_observation.v1",
        "generated_at_utc": RETRIEVED_AT,
        "status": "ok",
        "observations": [_rich_observation()],
        "failures": [],
    }
    path = tmp_path / "latest_observation.json"
    path.write_text(json.dumps(latest), encoding="utf-8")
    monkeypatch.setattr("scripts.m5k_common.LATEST_OBSERVATION_PATH", path)
    monkeypatch.setattr("scripts.m5k_common.REPO_ROOT", tmp_path)

    payload = read_latest_observation()

    assert payload["status"] == "ok"
    assert payload["content"]["observations"][0]["price_like_value"] == 1000.0
    assert payload["content"]["observations"][0]["twse_mis_rich_facts"]["ai_exposure_policy"]["safe_for_ai_context"] is False


def test_watchlist_rows_ignore_twse_mis_rich_facts_for_last_observation():
    obs = _rich_observation()
    obs["twse_mis_rich_facts"]["price_facts"]["last_value"] = 9999.0
    rows = build_watchlist_rows(_watchlist(), {"observations": [obs]})

    assert rows[0]["last_observation"] == 1000.0
    assert rows[0]["source"] == "TWSE_MIS"
    assert rows[0]["status"] == "observed"
    assert "twse_mis_rich_facts" not in rows[0]


def test_watchlist_rows_preserve_reference_only_status_from_top_level_fields():
    obs = _rich_observation(z="-", y="995.00", pz="1001.00")
    rows = build_watchlist_rows(_watchlist(), {"observations": [obs]})

    assert obs["status"] == "reference_value_only"
    assert obs["reference_only"] is True
    assert rows[0]["last_observation"] == 995.0
    assert rows[0]["status"] == "observed"


def test_non_twse_mis_normalizers_do_not_attach_rich_facts():
    generic = normalize_observation(
        symbol="X", source="OTHER", adapter_id="other", status="ok", retrieved_at_utc=RETRIEVED_AT, price_like_value=1.0
    )
    taifex = normalize_taifex_row(
        {"CLastPrice": "100", "CDate": "20260707", "CTime": "120000", "Status": "open", "SymbolID": "TXF202607"},
        {"symbol": "TX", "instrument_type": "futures", "contract_selector": "front_month"},
        RETRIEVED_AT,
    )
    failure = normalize_failure(symbol="X", source="OTHER", adapter_id="other", reason="missing")

    assert "twse_mis_rich_facts" not in generic
    assert "twse_mis_rich_facts" not in taifex
    assert "twse_mis_rich_facts" not in failure


def test_twse_mis_observation_keeps_ai_context_unsafe_and_top_level_fallbacks():
    obs = _rich_observation(z="-", y="995.00", pz="1001.00", ps="999")

    assert obs["price_like_value"] == 995.0
    assert obs["price_source_field"] == "y"
    assert obs["reference_only"] is True
    facts = obs["twse_mis_rich_facts"]
    assert facts["ai_exposure_policy"]["safe_for_ai_context"] is False
    assert facts["limit_or_reference_facts"]["raw_pz"] == "1001.00"
    assert obs["price_like_value"] != float(facts["limit_or_reference_facts"]["raw_pz"])


def test_conversation_handoff_does_not_promote_twse_mis_rich_facts():
    context = build_conversation_context(_watchlist(), {"status": "ok", "observations": [_rich_observation()], "failures": []})
    rendered = json.dumps(context, ensure_ascii=False).lower()

    assert "twse_mis_rich_facts" not in rendered
    assert context["governance"]["recommendation"] is False
    assert context["governance"]["buy_sell_hold"] is False
    assert context["ai_guidance_summary"]["trading_recommendation"] is False


def test_source_health_and_capabilities_tolerate_rich_facts_without_promotion():
    obs = _rich_observation()
    report = build_report(execution_mode="check_only", live_result={"observations": [obs], "failures": []})
    caps = source_capabilities()

    assert classify_observation(obs) in {"healthy", "degraded"}
    check_2330 = next(c for c in report["checks"] if c["target"] == "2330")
    assert check_2330["source_family"] == "TWSE_MIS listed stock route"
    assert "twse_mis_rich_facts" not in json.dumps(check_2330, ensure_ascii=False)
    assert caps["governance"]["trading_signal"] is False


def test_fastapi_and_mcp_helpers_tolerate_rich_facts_without_ai_promotion(monkeypatch):
    latest = {"status": "ok", "observations": [_rich_observation()], "failures": []}

    import server.main as fastapi_main
    import server.mcp_server as mcp_server

    monkeypatch.setattr(fastapi_main, "_m5k_read_latest_observation", lambda: latest)
    monkeypatch.setattr(mcp_server, "_m5k_read_latest_observation", lambda: latest)
    monkeypatch.setattr(fastapi_main, "_m5k_load_json", lambda path: _watchlist())
    monkeypatch.setattr(mcp_server, "_m5k_load_json", lambda path: _watchlist())

    api_latest = fastapi_main.get_m5k_latest_live_observation()
    api_context = fastapi_main.get_conversation_context()["content"]
    mcp_latest = {"tool": "get_m5k_latest_observation", **mcp_server._m5k_read_latest_observation()}
    mcp_context = mcp_server.get_conversation_context_tool()["content"]

    assert api_latest["observations"][0]["twse_mis_rich_facts"]["ai_exposure_policy"]["safe_for_ai_context"] is False
    assert "twse_mis_rich_facts" not in json.dumps(api_context, ensure_ascii=False)
    assert mcp_latest["observations"][0]["price_like_value"] == 1000.0
    assert "twse_mis_rich_facts" not in json.dumps(mcp_context, ensure_ascii=False)


def test_empty_rich_facts_contract_is_not_ai_safe():
    facts = build_empty_twse_mis_rich_facts()
    assert facts["ai_exposure_policy"]["safe_for_ai_context"] is False
