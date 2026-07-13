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
    assert "strike=20000" in md and "option_type=call" in md
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

def test_real_m8c01_txo_option_type_call_is_normalized():
    obs = build_taifex_mis_m8_observations({"observations":[raw(inst="option", option_type="call", runtime_symbol_id="TXO20260720000C-O")]})[0]
    assert obs["observation_valid"] is True
    assert obs["safe_fields"]["contract_identity"]["option_type"] == "call"


def test_missing_source_id_and_invalid_month_fail_closed():
    missing = raw(); missing.pop("source_id")
    bad_month = raw(contract_month_or_week="202613")
    observations = build_taifex_mis_m8_observations({"observations":[missing, bad_month]})
    assert all(o["observation_valid"] is False for o in observations)
    assert all("price" not in o["safe_fields"] for o in observations)


def test_mode1_with_status_or_book_provenance_only_is_accepted():
    obs = raw(field_provenance={"status":{"source":"sockjs_mode_1","field":"145"}}, normalized_field_candidates={"best_bid":"99","best_ask":"100","canonicalization_status":"candidate_families_agree"})
    adapted = build_taifex_mis_m8_observations({"observations":[obs]})[0]
    assert adapted["accepted_mode_1_present"] is True
    assert adapted["observation_valid"] is True


def test_execution_selector_ok_marks_mode1_even_without_value_provenance():
    obs = raw(field_provenance={})
    adapted = build_taifex_mis_m8_observations({"observations":[obs], "selector_results":[{"status":"ok", "runtime_symbol_id":"TXF202607-F"}]})[0]
    assert adapted["accepted_mode_1_present"] is True


def test_nested_raw_payload_truevalues_numeric_qid_blocks_values():
    obs = raw(extra={"raw_payload":{"125":"1"}, "trueValues":[1]})
    adapted = build_taifex_mis_m8_observations({"observations":[obs]})[0]
    assert adapted["observation_valid"] is False
    assert "forbidden_nested_source_field_present" in adapted["adapter_validation"]["errors"]
    assert "price" not in adapted["safe_fields"]


def test_ncdr_dgpa_cannot_establish_taifex_special_closure():
    currentness = dict(raw()["currentness"], overall_ai_currentness="special_closure_latest_completed", special_closure_evidence={"source_family":"NCDR_DGPA", "authority_level":"official", "target_date_matches":True, "target_date":"2026-07-13"})
    ctx = built("special_closure_latest_completed", currentness=currentness)["instrument_contexts"][0]["contexts"][0]
    assert ctx["metadata_only"] is True
    assert ctx["withhold_market_values_from_conversation"] is True


def test_preopen_halted_closed_unresolved_are_not_stale_summary_or_caveat():
    for status in ["preopen", "halted", "closed_session_latest_completed", "market_phase_unresolved"]:
        ctx = built(status)
        assert ctx["freshness_summary"]["has_stale_sources"] is False
        md = build_controlled_conversation_context(ctx)["sections"][0]["markdown"]
        assert "stale source must not be described" not in md


def test_invalid_instrument_markdown_is_metadata_not_futures():
    obs = build_taifex_mis_m8_observations({"observations":[raw(instrument_type="weird", runtime_symbol_id="BAD")]})
    convo = build_controlled_conversation_context(build_multi_source_market_context(obs, REG_TRUE, now_utc="2026-07-13T01:00:05Z"))
    md = convo["sections"][0]["markdown"]
    assert "metadata-only selector record" in md
    assert "bounded futures snapshot" not in md


def test_failed_selector_list_identity_is_stable_for_grouping():
    observations = build_taifex_mis_m8_observations({"observations":[],"selector_results":[{"selector":["TX", "202607"],"status":"snapshot_incomplete"}],"transport_summary":{}})
    ctx = build_multi_source_market_context(observations, REG_TRUE, now_utc="2026-07-13T01:00:05Z")
    assert ctx["instrument_contexts"][0]["symbol"] == "TX:202607"

def _contains_key(obj, key):
    if isinstance(obj, dict):
        return key in obj or any(_contains_key(v, key) for v in obj.values())
    if isinstance(obj, list):
        return any(_contains_key(v, key) for v in obj)
    return False


def test_invalid_metadata_contract_identity_containers_are_removed():
    obs = raw(requested_product_id={"raw_payload":"secret"}, raw_CTime={"bad":"container"}, source_status_code=["bad"])
    adapted = build_taifex_mis_m8_observations({"observations":[obs]})[0]
    assert adapted["observation_valid"] is False
    assert adapted["safe_fields"]["contract_identity"]["requested_product_id"] is None
    assert adapted["safe_fields"]["source_time"]["ctime_raw"] is None
    assert adapted["safe_fields"]["source_status_code"] is None
    assert not _contains_key(adapted["safe_fields"], "raw_payload")


def test_invalid_container_timestamp_cannot_become_primary():
    ctx = built("active_session_fresh_liveish", ts={"bad":"timestamp"})
    item = ctx["instrument_contexts"][0]["contexts"][0]
    assert item["primary_context_allowed"] is False
    assert item["metadata_only"] is True


def test_container_market_values_and_nan_negative_strike_are_withheld():
    obs = raw(inst="option", strike_price="NaN", normalized_field_candidates={"last_price":{"bad":"container"}, "total_volume":-1})
    adapted = build_taifex_mis_m8_observations({"observations":[obs]})[0]
    assert adapted["observation_valid"] is False
    assert "price" not in adapted["safe_fields"]
    assert adapted["safe_fields"]["contract_identity"]["strike_price"] is None


def test_fake_provenance_cannot_establish_mode1_but_status_book_can():
    fake = build_taifex_mis_m8_observations({"observations":[raw(field_provenance={"fake":{"source":"sockjs_mode_1"}})]})[0]
    assert fake["accepted_mode_1_present"] is False
    assert fake["observation_valid"] is False
    good = build_taifex_mis_m8_observations({"observations":[raw(field_provenance={"status":{"source":"sockjs_mode_1"}, "bid_family_1":{"source":"sockjs_mode_1"}})]})[0]
    assert good["accepted_mode_1_present"] is True
    assert good["observation_valid"] is True


def test_wrong_special_closure_evidence_type_rejected():
    currentness = dict(raw()["currentness"], overall_ai_currentness="special_closure_latest_completed", special_closure_evidence={"source_family":"TAIFEX", "authority_level":"official_documented", "evidence_type":"holiday", "target_date_matches":True, "target_date":"2026-07-13"})
    ctx = built("special_closure_latest_completed", currentness=currentness)["instrument_contexts"][0]["contexts"][0]
    assert ctx["metadata_only"] is True
    assert ctx["withhold_market_values_from_conversation"] is True


def test_structured_projection_has_no_recursive_raw_keys():
    obs = build_taifex_mis_m8_observations({"observations":[raw(extra={"safeish":{"trueValues":[1]}, "raw_payload":"x"})]})[0]
    convo = build_controlled_conversation_context(build_multi_source_market_context([obs], REG_TRUE, now_utc="2026-07-13T01:00:05Z"))
    projected = convo["sections"][0]["instrument_contexts"][0]["contexts"][0]
    for key in ["raw_payload", "trueValues", "125", "sockjs_frames", "rest_rows"]:
        assert not _contains_key(projected, key)


def test_actual_m8c01_decimal_observation_remains_valid_and_precision_preserved():
    from types import SimpleNamespace
    from decimal import Decimal
    from scripts.m8c_taifex_mis_observation import build_observation

    selector = SimpleNamespace(requested_product_id="TXO", instrument_type="option", session="regular", contract_month_or_week="202607", strike_price=Decimal("20000"), option_type="call")
    resolved = {"mis_cid":"TXO20260720000C", "runtime_symbol_id":"TXO20260720000C-O", "network_scope":"bounded", "retained_scope":"normalized_only"}
    mode1 = {"125":"12.345678901234567890", "129":"12.0", "404":"10", "143":"09:00:00", "144":"2026/07/13", "145":"active_regular_trading", "101":"12.3", "102":"12.4", "113":"1", "114":"2", "743":"12.3", "744":"12.4", "745":"1", "746":"2"}
    actual = build_observation(selector, resolved, mode1_quote=mode1, evaluation_time_asia_taipei="2026-07-13T09:00:05+08:00")
    assert isinstance(actual["normalized_field_candidates"]["last_price"], Decimal)
    adapted = build_taifex_mis_m8_observations({"observations":[actual], "selector_results":[{"status":"ok", "runtime_symbol_id":"TXO20260720000C-O"}]})[0]
    assert adapted["observation_valid"] is True
    assert adapted["adapter_validation"]["source_timestamp_valid"] is True
    assert adapted["adapter_validation"]["contract_identity_valid"] is True
    assert adapted["safe_fields"]["price"]["last"] == "12.345678901234567890"
    assert adapted["safe_fields"]["contract_identity"]["strike_price"] == "20000"


def test_malformed_scalar_timestamp_cannot_expose_supporting_values():
    observations = build_taifex_mis_m8_observations({"observations":[raw("market_phase_unresolved", ts="not-a-time")]})
    ctx = build_multi_source_market_context(observations, REG_TRUE, now_utc="2026-07-13T01:00:05Z")
    projected = build_controlled_conversation_context(ctx)["sections"][0]["instrument_contexts"][0]["contexts"][0]
    assert projected["metadata_only"] is True
    assert projected["safe_fields"]["source_time"]["source_timestamp"] is None
    assert "price" not in projected["safe_fields"]


def test_invalid_month_and_session_normalize_to_null_in_metadata():
    adapted = build_taifex_mis_m8_observations({"observations":[raw(contract_month_or_week="202613", session="after_hours")]})[0]
    ident = adapted["safe_fields"]["contract_identity"]
    assert adapted["observation_valid"] is False
    assert adapted["adapter_validation"]["contract_identity_valid"] is False
    assert ident["contract_month_or_week"] is None
    assert ident["session"] is None


def test_direct_taifex_builder_bypass_fails_closed_and_recursively_scrubs_raw_fields():
    direct = {
        "source_id":"TAIFEX_MIS", "source_family":"TAIFEX_MIS", "market":"taifex", "symbol":"TXF202607-F", "instrument_type":"futures",
        "context_type":"official_derivatives_futures_liveish_snapshot", "source_timestamp":"2026-07-13T09:00:00+08:00", "session":"regular",
        "currentness":{"overall_ai_currentness":"active_session_fresh_liveish"},
        "safe_fields":{"contract_identity":{"runtime_symbol_id":"TXF202607-F", "raw_payload":{"125":"100"}}, "source_time":{"source_timestamp":"2026-07-13T09:00:00+08:00"}, "price":{"last":"100"}, "raw_payload":"secret"},
    }
    ctx = build_multi_source_market_context([direct], REG_TRUE, now_utc="2026-07-13T01:00:05Z")
    item = ctx["instrument_contexts"][0]["contexts"][0]
    assert item["safe_for_ai_context"] is False
    assert item["metadata_only"] is True
    assert "price" not in item["safe_fields"]
    assert not _contains_key(item["safe_fields"], "raw_payload")
    projected = build_controlled_conversation_context(ctx)["sections"][0]["instrument_contexts"][0]["contexts"][0]
    assert "price" not in projected["safe_fields"]
    assert not _contains_key(projected, "raw_payload")


def test_invalid_canonicalization_status_container_is_unresolved_not_projected_book():
    adapted = build_taifex_mis_m8_observations({"observations":[raw(normalized_field_candidates={"last_price":"100", "best_bid":"99", "best_ask":"101", "canonicalization_status":{"bad":"container"}})]})[0]
    assert adapted["safe_fields"]["top_of_book"]["canonicalization_status"] == "top_of_book_field_family_unresolved"
    assert adapted["safe_fields"]["top_of_book"]["best_bid"] is None
    valid = raw(normalized_field_candidates={"last_price":"100", "reference_price":"99", "total_volume":"1", "best_bid":"99", "best_ask":"101", "canonicalization_status":"unknown"})
    adapted_valid = build_taifex_mis_m8_observations({"observations":[valid]})[0]
    assert adapted_valid["safe_fields"]["top_of_book"]["canonicalization_status"] == "top_of_book_field_family_unresolved"
    assert adapted_valid["safe_fields"]["top_of_book"]["best_bid"] is None


def test_real_m8c01_txo_missing_ctime_remains_valid_metadata_only_source_timestamp_unresolved():
    from types import SimpleNamespace
    from scripts.m8c_taifex_mis_observation import build_observation

    selector = SimpleNamespace(requested_product_id="TXO", instrument_type="option", session="regular", contract_month_or_week="202607", strike_price="20000", option_type="call")
    resolved = {"mis_cid":"TXO20260720000C", "runtime_symbol_id":"TXO20260720000C-O", "network_scope":"bounded", "retained_scope":"normalized_only"}
    mode1 = {"125":"12.3", "129":"12.0", "404":"10", "144":"2026/07/13", "145":"active_regular_trading", "101":"12.2", "102":"12.4", "743":"12.2", "744":"12.4"}
    actual = build_observation(selector, resolved, mode1_quote=mode1, evaluation_time_asia_taipei="2026-07-13T09:00:05+08:00")
    assert actual["raw_CTime"] is None
    assert actual["source_timestamp_asia_taipei"] is None
    assert actual["currentness"]["overall_ai_currentness"] == "source_timestamp_unresolved"

    adapted = build_taifex_mis_m8_observations({"observations":[actual], "selector_results":[{"status":"ok", "runtime_symbol_id":"TXO20260720000C-O"}]})[0]
    assert adapted["observation_valid"] is True
    assert adapted["adapter_validation"]["source_timestamp_valid"] is False
    assert "source_timestamp_invalid_or_missing" not in adapted["adapter_validation"]["errors"]
    assert "price" not in adapted["safe_fields"]

    ctx = build_multi_source_market_context([adapted], REG_TRUE, now_utc="2026-07-13T01:00:05Z")
    item = ctx["instrument_contexts"][0]["contexts"][0]
    assert item["overall_ai_currentness"] == "source_timestamp_unresolved"
    assert item["taifex_mis_role_detail"] == "source_timestamp_unresolved"
    assert item["metadata_only"] is True
    assert item["withhold_market_values_from_conversation"] is True
    assert not any("adapter envelope" in c for c in item["caveats"])


def test_trusted_invalid_adapter_metadata_is_not_bypass_and_preserves_failure_reason():
    failure = build_taifex_mis_m8_observations({"status":"partial_source_success", "observations":[], "selector_results":[{"selector":"bad", "status":"snapshot_incomplete", "runtime_symbol_id":"BAD-F"}], "transport_summary":{}})[0]
    assert failure["observation_valid"] is False
    ctx = build_multi_source_market_context([failure], REG_TRUE, now_utc="2026-07-13T01:00:05Z")
    item = ctx["instrument_contexts"][0]["contexts"][0]
    assert item["source_unavailable"] is True
    assert item["metadata_only"] is True
    assert item["freshness_assessment"] == "source_unavailable"
    assert item["source_unavailable_reason"] == "selector_result_snapshot_incomplete"
    assert "selector_result_snapshot_incomplete" in item["caveats"]
    assert not any("adapter envelope" in c for c in item["caveats"])


def test_missing_envelope_and_validation_observation_mismatch_are_blocked():
    direct = {"source_id":"TAIFEX_MIS", "safe_fields":{"contract_identity":{"runtime_symbol_id":"TXF202607-F"}, "price":{"last":"100"}}, "currentness":{"overall_ai_currentness":"active_session_fresh_liveish"}}
    direct_ctx = build_multi_source_market_context([direct], REG_TRUE, now_utc="2026-07-13T01:00:05Z")["instrument_contexts"][0]["contexts"][0]
    assert direct_ctx["metadata_only"] is True
    assert "price" not in direct_ctx["safe_fields"]
    assert any("adapter envelope" in c for c in direct_ctx["caveats"])

    mismatch = build_taifex_mis_m8_observations({"observations":[raw()]})[0]
    mismatch["adapter_validation"] = dict(mismatch["adapter_validation"], valid=False)
    mismatch_ctx = build_multi_source_market_context([mismatch], REG_TRUE, now_utc="2026-07-13T01:00:05Z")["instrument_contexts"][0]["contexts"][0]
    assert mismatch_ctx["metadata_only"] is True
    assert "price" not in mismatch_ctx["safe_fields"]
    assert any("adapter envelope" in c for c in mismatch_ctx["caveats"])


def test_numeric_product_and_cid_identity_values_are_rejected():
    adapted = build_taifex_mis_m8_observations({"observations":[raw(requested_product_id=123, mis_cid=456)]})[0]
    assert adapted["observation_valid"] is False
    assert "invalid_bounded_string_requested_product_id" in adapted["adapter_validation"]["errors"]
    assert "invalid_bounded_string_mis_cid" in adapted["adapter_validation"]["errors"]
    assert adapted["safe_fields"]["contract_identity"]["requested_product_id"] is None
    assert adapted["safe_fields"]["contract_identity"]["mis_cid"] is None
