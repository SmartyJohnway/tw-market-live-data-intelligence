from __future__ import annotations
from scripts.m8r_bounded_market_context_request import compile_market_context_execution_plan, build_approval_artifact
from scripts.m8r_one_shot_market_context_orchestrator import execute_approved_market_context_plan
from scripts.m8r_ai_market_context_package import build_ai_market_context_package

NOW="2026-07-15T00:00:00Z"

def make_plan(source, target, contexts):
    req={"schema_version":"m8r_bounded_market_context_request.v1","request_id":"e2e","targets":[target],"requested_context_types":contexts,"requested_source_families":[source],"output_policy":{"artifact_root":"research/m8r/test"}}
    return compile_market_context_execution_plan(req, created_at_utc=NOW)

def test_e2e_twse_openapi_fake_production_adapter_to_ai_package(monkeypatch):
    from scripts import m8r_production_source_adapters as adapters
    monkeypatch.setattr(adapters,"execute_twse_official_eod_adapter",lambda syms:{"observations":[{"source_id":"TWSE_OPENAPI","symbol":"2330","market":"listed","instrument_type":"equity","trade_date":"2026-07-14","retrieved_at_utc":NOW,"price":{"close":"100"},"activity":{},"caveats":[]}]})
    p=make_plan("TWSE_OPENAPI", {"market":"TWSE","instrument_type":"equity","symbol":"2330"}, ["official_eod_reference"])
    out=execute_approved_market_context_plan(p, build_approval_artifact(p, approved_at_utc=NOW, single_use=False), execution_time_utc=NOW, allow_network=True)
    pkg=build_ai_market_context_package(out, generated_at_utc=NOW)
    assert out["execution_status"] in {"ready","ready_with_caveats"}
    assert pkg["schema_version"]=="ai_market_context.v1"
    assert pkg["production_readiness"]["production_executor_adapters_ready"] is True
    assert pkg["production_readiness"]["production_live_execution_ready"] is False
    assert pkg["source_contexts"][0]["timing_class"]=="official_eod"


def test_e2e_taifex_openapi_fake_production_adapter_to_ai_package(monkeypatch):
    from scripts import m8r_production_source_adapters as adapters
    monkeypatch.setattr(adapters,"execute_taifex_openapi_refresh",lambda **kw:{"observations":[{"source_id":"TAIFEX_OPENAPI","source_family":"TAIFEX_OPENAPI","symbol":"TX","instrument_type":"future","context_type":"official_derivatives_futures_eod","market":"TAIFEX","safe_fields":{},"timing_class":"official_statistics_eod","authority_level":"official_documented","retrieved_at_utc":NOW,"caveats":[]}]})
    target={"market":"TAIFEX","instrument_type":"future","symbol":"TX","expiry":"202607","contract_type":"monthly","session":"regular"}
    p=make_plan("TAIFEX_OPENAPI", target, ["official_eod_reference"])
    out=execute_approved_market_context_plan(p, build_approval_artifact(p, approved_at_utc=NOW, single_use=False), execution_time_utc=NOW, allow_network=True)
    pkg=build_ai_market_context_package(out, generated_at_utc=NOW)
    assert out["operation_results"][0]["returned_identity"]["expiry"]=="202607"
    assert pkg["production_readiness"]["live_validation_completed"] is False
