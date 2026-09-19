import json
from pathlib import Path
import jsonschema
from scripts.phase_g.mops_monthly_revenue import execute

TARGET={"canonical_target_id":"TWSE:2330","market":"TWSE","security_code":"2330","security_name_zh":"台積電"}
HEAD="出表日期,資料年月,公司代號,公司名稱,營業收入-當月營收,營業收入-上月營收,營業收入-去年當月營收,營業收入-上月比較增減(%),營業收入-去年同月增減(%),累計營業收入-當月累計營收,累計營業收入-去年累計營收,累計營業收入-前期比較增減(%),備註\n"
ROW="1150915,11508,2330,台積電,100,-2,90,,11.1,800,700,,官方備註\n"
def run(payload=HEAD+ROW, **kwargs): return execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=kwargs.get("csv",lambda _:payload),json_fetcher=kwargs.get("jsonp",lambda _:"[]"))[0]
def test_d01_d03_d04_d05_d06_values_signed_null_note_and_roc_dates():
    result=run(); value=result["value"]
    assert result["status"]=="available" and result["coverage"]=={"mode":"latest_available_reporting_period","reporting_period":"2026-08","source_report_date":"2026-09-15"}
    assert value["currency"]=="TWD" and value["unit"]=="thousand" and value["previous_month_revenue"]==-2 and value["mom_pct"] is None and value["ytd_yoy_pct"] is None and value["note"]=="官方備註"
def test_d02_tpex_route():
    target={**TARGET,"canonical_target_id":"TPEX:6488","market":"TPEX","security_code":"6488"}; result=execute([target],"TPEX",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:(HEAD+ROW.replace("2330","6488",1)),json_fetcher=lambda _:"[]")[0]
    assert result["status"]=="available" and result["source"]["source_contract_id"]=="t187ap05_O"
def test_d07_b08_healthy_missing_and_name_mismatch():
    assert run(HEAD+ROW.replace("2330","2317",1).replace("台積電","其他",1))["status"]=="not_yet_available"
    assert run(HEAD+ROW.replace("2330","2317",1))["status"]=="binding_failed"
def test_d08_d09_d10_d11_transport_and_conflict_contracts():
    assert run(HEAD+ROW+ROW.replace(",100,",",101,"))["status"]=="binding_failed"
    calls=[]; assert run(csv=lambda _:calls.append("csv") or HEAD+ROW,jsonp=lambda _:calls.append("json"))["source"]["fallback_used"] is False and calls==["csv"]
    fallback=run(csv=lambda _:(_ for _ in ()).throw(OSError()),jsonp=lambda _:[dict(zip(HEAD.strip().split(","),ROW.strip().split(",")))]); assert fallback["status"]=="available" and fallback["source"]["transport"]=="official_json_openapi"
    assert run(csv=lambda _:"",jsonp=lambda _:"[]")["status"]=="source_failed"
def test_d12_d13_d14_schema_and_target_bounded_output():
    result=run(HEAD+ROW+ROW.replace("2330","2317",1).replace("台積電","其他",1)); assert result["coverage"]["reporting_period"]=="2026-08" and result["value"]["currency"]=="TWD"
    jsonschema.validate(result,json.loads((Path(__file__).resolve().parents[2]/"schemas/phase_g_monthly_revenue_operation_evidence.v1.schema.json").read_text()))
