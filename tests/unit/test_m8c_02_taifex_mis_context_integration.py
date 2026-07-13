import importlib

from scripts.m8c_taifex_mis_context_adapter import build_taifex_mis_m8_observations
from scripts.m8_multi_source_context_builder import build_multi_source_market_context
from scripts.m8_controlled_conversation_context import build_controlled_conversation_context

REG_TRUE = {"sources": [{"source_id":"TAIFEX_MIS","source_family":"TAIFEX_MIS","authority_level":"official_undocumented","timing_class":"liveish_intraday_snapshot","ai_context_allowed":True,"ai_exposure_level":"controlled_caveated_safe_fields","runtime_executable":True,"caveats":["not realtime guaranteed"]},{"source_id":"TAIFEX_OPENAPI","source_family":"TAIFEX_OPENAPI","authority_level":"official_documented","timing_class":"official_statistics_eod","ai_context_allowed":True,"ai_exposure_level":"caveated_context_allowed","runtime_executable":True,"caveats":[]}]}
REG_FALSE = {"sources": [dict(REG_TRUE["sources"][0], ai_context_allowed=False, ai_exposure_level="metadata_only"), REG_TRUE["sources"][1]]}

def raw(status="active_session_fresh_liveish", ts="2026-07-13T09:00:00+08:00", inst="future", **overrides):
    cur = {"overall_ai_currentness":status,"market_phase":"active_regular_trading","source_timestamp_state":"resolved" if ts else "unresolved","session_alignment":"aligned","quote_age_state":"fresh" if status=="active_session_fresh_liveish" else "aging","retrieved_at_freshness_ignored_for_upgrade":True}
    data = {"source_id":"TAIFEX_MIS","requested_product_id":"TX","mis_cid":"TXF202607","runtime_symbol_id":"TXF202607-F" if inst=="future" else "TXO20260720000C-O","instrument_type":inst,"session":"regular","contract_month_or_week":"202607","strike_price":"20000" if inst=="option" else None,"option_type":"C" if inst=="option" else None,"raw_CDate":"2026/07/13","raw_CTime":"09:00:00" if ts else None,"source_timestamp_asia_taipei":ts,"source_status_code":"active_regular_trading","currentness":cur,"normalized_field_candidates":{"last_price":"100","reference_price":"99","total_volume":"10","best_bid":"99.5","best_ask":"100.5","canonicalization_status":"candidate_families_agree"},"field_provenance":{"last_price":{"source":"sockjs_mode_1","field":"125"}},"caveats":[],"raw_payload_retained":False}
    data.update(overrides)
    return data

def built(status, ts="2026-07-13T09:00:00+08:00", registry=REG_TRUE, **overrides):
    obs = build_taifex_mis_m8_observations({"observations":[raw(status, ts, **overrides)]})
    return build_multi_source_market_context(obs, registry, now_utc="2026-07-13T01:00:05Z")

def test_currentness_precedence_retrieved_at_cannot_upgrade_closed_or_unresolved():
    for status in ["closed_session_latest_completed", "market_phase_unresolved", "source_timestamp_unresolved"]:
        ctx = built(status, None if status == "source_timestamp_unresolved" else "2026-07-13T09:00:00+08:00")
        item = ctx["instrument_contexts"][0]["contexts"][0]
        assert item["freshness_assessment"] != "fresh_intraday_snapshot"
        assert item["primary_context_allowed"] is False
        assert "TAIFEX MIS retrieved_at_utc must never upgrade source currentness" in item["caveats"]

def test_active_fresh_primary_requires_all_axes_and_mode1_provenance():
    fresh = built("active_session_fresh_liveish")["instrument_contexts"][0]["contexts"][0]
    assert fresh["freshness_assessment"] == "fresh_intraday_snapshot"
    assert fresh["primary_context_allowed"] is True
    bad = built("active_session_fresh_liveish", currentness=dict(raw()["currentness"], quote_age_state="stale"))["instrument_contexts"][0]["contexts"][0]
    assert bad["freshness_assessment"] == "source_specific_currentness_unresolved"
    assert bad["metadata_only"] is True
    no_mode1 = built("active_session_fresh_liveish", field_provenance={})["instrument_contexts"][0]["contexts"][0]
    assert no_mode1["metadata_only"] is True

def test_aging_stale_supporting_only_and_summaries_distinguish_states():
    aging = built("active_session_aging_liveish")
    item = aging["instrument_contexts"][0]["contexts"][0]
    assert item["freshness_assessment"] == "caveated_intraday_snapshot"
    assert item["supporting_context_only"] is True
    assert item["primary_context_allowed"] is False
    assert aging["freshness_summary"]["has_taifex_mis_aging_liveish"] is True
    stale = built("active_session_stale_liveish")
    assert stale["freshness_summary"]["has_taifex_mis_stale_liveish"] is True

def test_strict_adapter_validation_unknowns_fail_closed_without_defaulting_to_futures():
    obs = build_taifex_mis_m8_observations({"observations":[raw(instrument_type="unknown", runtime_symbol_id="BAD") ]})[0]
    assert obs["observation_valid"] is False
    assert obs["instrument_type"] == "unknown"
    assert obs["context_type"] is None
    assert "price" not in obs["safe_fields"]

def test_adapter_omits_raw_qids_truevalues_payload_and_only_canonical_book():
    obs = build_taifex_mis_m8_observations({"observations":[raw()]})[0]
    text = str(obs)
    assert "trueValues" in obs["omitted_fields"]
    assert "trueValues" not in str(obs["safe_fields"])
    assert "raw_payload" not in obs["safe_fields"]
    assert "125" not in text
    assert "family_101" not in text
    assert obs["safe_fields"]["top_of_book"]["best_bid"] == "99.5"

def test_projection_formats_values_when_policy_enabled_and_withholds_missing_ctime_values():
    observations = build_taifex_mis_m8_observations({"observations":[raw(), raw("source_timestamp_unresolved", None, inst="option")]})
    convo = build_controlled_conversation_context(build_multi_source_market_context(observations, REG_TRUE, now_utc="2026-07-13T01:00:05Z"))
    md = convo["sections"][0]["markdown"]
    assert "TAIFEX MIS bounded futures snapshot" in md
    assert "TAIFEX MIS bounded options snapshot" in md
    assert "strike=20000" in md and "option_type=C" in md
    assert "last=100" in md
    opt = convo["sections"][0]["instrument_contexts"][1]["contexts"][0]
    assert "price" not in opt["safe_fields"]
    assert "raw_payload" not in md and "trueValues" not in md and "safe_fields={" not in md

def test_policy_disabled_keeps_metadata_but_withholds_taifex_values():
    observations = build_taifex_mis_m8_observations({"observations":[raw()]})
    convo = build_controlled_conversation_context(build_multi_source_market_context(observations, REG_FALSE, now_utc="2026-07-13T01:00:05Z"))
    ctx = convo["sections"][0]["instrument_contexts"][0]["contexts"][0]
    assert ctx["safe_for_ai_context"] is False
    assert {"contract_identity", "source_time", "source_status_code", "currentness"} <= set(ctx["safe_fields"])
    assert "price" not in ctx["safe_fields"] and "activity" not in ctx["safe_fields"] and "top_of_book" not in ctx["safe_fields"]

def test_missing_selector_metadata_contexts_are_preserved_without_values():
    observations = build_taifex_mis_m8_observations({"status":"partial_source_success","observations":[raw()],"selector_results":[{"selector":"bad","status":"snapshot_incomplete","runtime_symbol_id":"BAD-F"}],"transport_summary":{"missing_symbols":["MISS-F"]}})
    failures = [o for o in observations if o.get("source_unavailable")]
    assert len(failures) == 2
    assert all("price" not in f["safe_fields"] for f in failures)

def test_taifex_mis_and_openapi_coexist_distinct_groups():
    mis = build_taifex_mis_m8_observations({"observations":[raw()]})[0]
    eod = {"source_id":"TAIFEX_OPENAPI","source_family":"TAIFEX_OPENAPI","context_type":"official_derivatives_futures_eod_reference","market":"taifex","symbol":"TXF202607-F","instrument_type":"futures","trade_date":"2026-07-10","safe_fields":{"payload":{},"contract_identity":{"product_id":"TX","contract_month_or_week":"202607"},"currentness":{"status":"latest_completed_trade_date"}},"retrieved_at_utc":"2026-07-13T01:00:01Z"}
    ctx = build_multi_source_market_context([mis, eod], REG_TRUE, now_utc="2026-07-13T01:00:05Z")
    groups = {c["context_group"] for i in ctx["instrument_contexts"] for c in i["contexts"]}
    assert {"derivatives_liveish", "derivatives_official_eod"} <= groups
    assert ctx["freshness_summary"]["has_taifex_mis_observation"] is True

def test_imports_are_pure_no_network(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("network attempted")
    import requests
    monkeypatch.setattr(requests.sessions.Session, "request", boom)
    importlib.reload(importlib.import_module("scripts.m8c_taifex_mis_context_adapter"))
    importlib.reload(importlib.import_module("scripts.m8c_02_taifex_mis_context_integration"))
