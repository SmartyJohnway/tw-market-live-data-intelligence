from __future__ import annotations

from scripts import m8r_production_source_adapters as a

NOW="2026-07-15T00:00:00Z"

def op(source, route=None, context_type="liveish_observation"):
    return {"source_family":source,"route":route,"network_required":True,"context_type":context_type}
def stock(symbol="2330", market="TWSE", typ="equity"):
    return {"market":market,"instrument_type":typ,"symbol":symbol}
def future():
    return {"market":"TAIFEX","instrument_type":"future","symbol":"TX","derivative_identity":{"expiry":"202607","contract_type":"monthly","session":"regular"}}
def option():
    return {"market":"TAIFEX","instrument_type":"option","symbol":"TXO","derivative_identity":{"underlying":"TX","expiry":"202607","strike":"20000.0","call_put":"C","contract_type":"monthly","session":"regular"}}
def m8b_future_obs(**ci):
    ident={"product_id":"TX","contract_month_or_week":"202607","session":"regular",**ci}
    return {"source_id":"TAIFEX_OPENAPI","source_family":"TAIFEX_OPENAPI","product_id":ident.get("product_id"),"symbol":ident.get("product_id"),"contract_identity":ident,"safe_fields":{"contract_identity":ident},"timing_class":"official_derivatives_eod"}
def m8b_option_obs(**ci):
    ident={"product_id":"TXO","contract_month_or_week":"202607","strike_price":"20000","option_type":"call","session":"regular",**ci}
    return {"source_id":"TAIFEX_OPENAPI","source_family":"TAIFEX_OPENAPI","product_id":ident.get("product_id"),"symbol":ident.get("product_id"),"contract_identity":ident,"safe_fields":{"contract_identity":ident},"timing_class":"official_derivatives_eod"}

def test_registry_replaces_network_defaults():
    reg=a.build_production_executor_registry()
    for src in ["TWSE_MIS","TWSE_OPENAPI","TPEX_OPENAPI","TAIFEX_MIS","TAIFEX_OPENAPI"]:
        assert reg[(a.NETWORK_CLASS,src)].__name__ != "_blocked_default_executor"
    assert ("unknown","NOPE") not in reg

def test_twse_mis_mapping_and_identity(monkeypatch):
    calls=[]
    def fake(symbols, **kw):
        calls.append(symbols); return ([{"key":"tse_2330.tw","c":"2330","z":"100","y":"99","d":"20260715","t":"09:01:00"}], [], {})
    monkeypatch.setattr(a,"fetch_twse_mis_rows",fake)
    out=a.execute_twse_mis_operation(operation=op("TWSE_MIS","tse_2330.tw"),target=stock(),plan={},execution_time_utc=NOW,allow_network=True)
    assert out["status"]=="succeeded" and calls==[["tse_2330.tw"]]
    assert out["source_observation"]["timing_class"]=="liveish_intraday_snapshot"
    bad=a.execute_twse_mis_operation(operation=op("TWSE_MIS","otc_2330.tw"),target=stock(),plan={},execution_time_utc=NOW,allow_network=True)
    assert bad["status"]=="blocked"

def test_openapi_bounded_and_absent(monkeypatch):
    def twse(symbols): return {"observations":[{"source_id":"TWSE_OPENAPI","symbol":"2330","market":"listed","instrument_type":"equity","trade_date":"2026-07-14","retrieved_at_utc":NOW,"price":{},"activity":{},"caveats":[]},{"source_id":"TWSE_OPENAPI","symbol":"9999","market":"listed","instrument_type":"equity","trade_date":"2026-07-14","retrieved_at_utc":NOW,"price":{},"activity":{},"caveats":[]}]}
    monkeypatch.setattr(a,"execute_twse_official_eod_adapter",twse)
    out=a.execute_twse_openapi_operation(operation=op("TWSE_OPENAPI"),target=stock(),plan={},execution_time_utc=NOW,allow_network=True)
    assert out["status"]=="succeeded" and out["grouping"]["network_scope"]=="whole_market_endpoint"
    assert out["source_observation"]["symbol"]=="2330" and "9999" not in str(out)
    absent=a.execute_twse_openapi_operation(operation=op("TWSE_OPENAPI"),target=stock("1111"),plan={},execution_time_utc=NOW,allow_network=True)
    assert absent["issues"][0]["code"]=="target_not_present_in_source_result"

def test_openapi_retained_identity_validation(monkeypatch):
    def set_twse(row): monkeypatch.setattr(a,"execute_twse_official_eod_adapter",lambda syms:{"observations":[row]})
    base={"source_id":"TWSE_OPENAPI","symbol":"2330","market":"listed","instrument_type":"equity","trade_date":"2026-07-14","retrieved_at_utc":NOW,"price":{},"activity":{},"caveats":[]}
    set_twse(dict(base, market="tpex_otc")); assert a.execute_twse_openapi_operation(operation=op("TWSE_OPENAPI"),target=stock(),plan={},execution_time_utc=NOW,allow_network=True)["issues"][0]["code"]=="source_market_mismatch"
    set_twse(dict(base, instrument_type="etf")); assert a.execute_twse_openapi_operation(operation=op("TWSE_OPENAPI"),target=stock(),plan={},execution_time_utc=NOW,allow_network=True)["issues"][0]["code"]=="source_instrument_type_mismatch"
    set_twse(dict(base, source_id="TPEX_OPENAPI")); assert a.execute_twse_openapi_operation(operation=op("TWSE_OPENAPI"),target=stock(),plan={},execution_time_utc=NOW,allow_network=True)["issues"][0]["code"]=="source_identity_mismatch"

def test_tpex_market_guard_and_identity(monkeypatch):
    good={"source_id":"TPEX_OPENAPI","symbol":"6488","market":"tpex_otc","instrument_type":"equity","trade_date":"2026-07-14","retrieved_at_utc":NOW,"price":{},"activity":{},"caveats":[]}
    monkeypatch.setattr(a,"execute_tpex_official_eod_adapter",lambda syms:{"observations":[good]})
    assert a.execute_tpex_openapi_operation(operation=op("TPEX_OPENAPI"),target=stock("6488","TPEX"),plan={},execution_time_utc=NOW,allow_network=True)["status"]=="succeeded"
    monkeypatch.setattr(a,"execute_tpex_official_eod_adapter",lambda syms:{"observations":[dict(good, market="listed")]})
    assert a.execute_tpex_openapi_operation(operation=op("TPEX_OPENAPI"),target=stock("6488","TPEX"),plan={},execution_time_utc=NOW,allow_network=True)["issues"][0]["code"]=="source_market_mismatch"
    assert a.execute_tpex_openapi_operation(operation=op("TPEX_OPENAPI"),target=stock("2330","TWSE"),plan={},execution_time_utc=NOW,allow_network=True)["status"]=="blocked"

def test_taifex_mis_exact_identity_and_accounting(monkeypatch):
    def fake(**kw):
        assert kw["requested_contracts"]==[{"instrument_type":"future","requested_product_id":"TX","contract_month_or_week":"202607","session":"regular"}]
        return {"status":"successful_liveish_snapshot","observations":[{"instrument_type":"future","requested_product_id":"TX","runtime_symbol_id":"TXF202607","contract_month_or_week":"202607","session":"regular","source_timestamp_asia_taipei":"2026-07-15T09:01:00+08:00","currentness":{},"field_provenance":{"last_price":{"source":"sockjs_mode_1"}},"normalized_field_candidates":{"last_price":"1"}}]}
    monkeypatch.setattr(a,"execute_taifex_mis_snapshot",fake)
    out=a.execute_taifex_mis_operation(operation=op("TAIFEX_MIS"),target=future(),plan={},execution_time_utc=NOW,allow_network=True)
    assert out["status"]=="succeeded" and out["network_request_count"]==2 and out["returned_identity"]["expiry"]=="202607"
    bad=future(); bad["derivative_identity"]["contract_type"]="weekly"
    assert a.execute_taifex_mis_operation(operation=op("TAIFEX_MIS"),target=bad,plan={},execution_time_utc=NOW,allow_network=True)["network_attempted"] is False

def test_taifex_mis_option_identity_mismatches_and_underlying(monkeypatch):
    def run(obs):
        monkeypatch.setattr(a,"execute_taifex_mis_snapshot",lambda **kw:{"status":"successful_liveish_snapshot","observations":[obs]})
        return a.execute_taifex_mis_operation(operation=op("TAIFEX_MIS"),target=option(),plan={},execution_time_utc=NOW,allow_network=True)
    base={"instrument_type":"option","requested_product_id":"TXO","runtime_symbol_id":"TXO202607C20000","contract_month_or_week":"202607","strike_price":"20000","option_type":"call","session":"regular","source_timestamp_asia_taipei":"2026-07-15T09:01:00+08:00","currentness":{},"field_provenance":{"last_price":{"source":"sockjs_mode_1"}},"normalized_field_candidates":{"last_price":"1"}}
    out=run(base); assert out["status"]=="succeeded" and out["returned_identity"]["underlying"]=="TX"
    assert run(dict(base, requested_product_id="ABC", runtime_symbol_id="ABC202607C20000"))["issues"][0]["code"]=="source_identity_mismatch"
    assert run(dict(base, contract_month_or_week="202608", runtime_symbol_id="TXO202608C20000"))["issues"][0]["code"]=="source_identity_mismatch"
    assert run(dict(base, strike_price="21000", runtime_symbol_id="TXO202607C21000"))["issues"][0]["code"]=="source_identity_mismatch"
    assert run(dict(base, option_type="put", runtime_symbol_id="TXO202607P20000"))["issues"][0]["code"]=="source_identity_mismatch"
    unavailable=run(dict(base, requested_product_id="ZZO", runtime_symbol_id="ZZO202607C20000"))
    assert unavailable["issues"][0]["code"] in {"source_identity_mismatch","exact_option_underlying_not_returned"}
    assert unavailable.get("returned_identity",{}).get("underlying") is None

def test_taifex_openapi_identity_evidence_levels(monkeypatch):
    def run(obs, target=None, context_type="official_eod_reference"):
        monkeypatch.setattr(a,"execute_taifex_openapi_refresh",lambda **kw:{"observations":[obs]})
        return a.execute_taifex_openapi_operation(operation=op("TAIFEX_OPENAPI", context_type=context_type),target=target or future(),plan={},execution_time_utc=NOW,allow_network=True)
    no_identity={"source_id":"TAIFEX_OPENAPI","source_family":"TAIFEX_OPENAPI","symbol":"TX","safe_fields":{},"timing_class":"official_derivatives_eod"}
    assert run(no_identity)["issues"][0]["code"]=="exact_contract_identity_not_returned"
    assert run(m8b_future_obs(contract_month_or_week="202608"))["issues"][0]["code"]=="source_identity_mismatch"
    product_level={"source_id":"TAIFEX_OPENAPI","source_family":"TAIFEX_OPENAPI","product_id":"TX","symbol":"TX","safe_fields":{},"timing_class":"official_derivatives_eod"}
    product_out=run(product_level, context_type="official_statistical_reference")
    assert product_out["status"]=="succeeded" and product_out["source_observation"]["safe_fields"]["identity_level"]=="product_level"
    assert "expiry" not in product_out["returned_identity"]
    out=run(m8b_future_obs())
    assert out["status"]=="succeeded" and out["returned_identity"]=={"product":"TX","expiry":"202607","contract_type":"monthly","session":"regular"}
    opt_out=run(m8b_option_obs(), target=option())
    assert opt_out["status"]=="succeeded" and {k: opt_out["returned_identity"].get(k) for k in ["product","expiry","strike","call_put","contract_type","session"]} == {"product":"TXO","expiry":"202607","strike":"20000","call_put":"C","contract_type":"monthly","session":"regular"}
    missing_product={"source_id":"TAIFEX_OPENAPI","source_family":"TAIFEX_OPENAPI","contract_identity":{"contract_month_or_week":"202607","session":"regular"},"safe_fields":{"contract_identity":{"contract_month_or_week":"202607","session":"regular"}}}
    assert run(missing_product)["issues"][0]["code"]=="target_not_present_in_source_result"

def test_error_sanitization_and_network_gate(monkeypatch):
    assert a.execute_twse_mis_operation(operation=op("TWSE_MIS","tse_2330.tw"),target=stock(),plan={},execution_time_utc=NOW,allow_network=False)["issues"][0]["code"]=="network_execution_not_enabled"
    monkeypatch.setattr(a,"fetch_twse_mis_rows",lambda *a,**k: (_ for _ in ()).throw(TimeoutError("secret token url")))
    out=a.execute_twse_mis_operation(operation=op("TWSE_MIS","tse_2330.tw"),target=stock(),plan={},execution_time_utc=NOW,allow_network=True)
    assert out["issues"]==[{"code":"source_timeout","severity":"warning"}] and "secret" not in str(out)
