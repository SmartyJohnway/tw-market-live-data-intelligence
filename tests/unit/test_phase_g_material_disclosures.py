import json
from pathlib import Path
import jsonschema
from scripts.phase_g.mops_material_disclosures import execute

TARGET={"canonical_target_id":"TWSE:2330","market":"TWSE","security_code":"2330","security_name_zh":"台積電"}
CSV="公司代號,公司名稱,發言日期,發言時間,主旨,說明\n2330,台積電,1150915,65728,測試,內容\n"

def test_c01_c07_csv_exact_binding_and_five_digit_time():
    result=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:CSV,json_fetcher=lambda _: (_ for _ in ()).throw(AssertionError()))[0]
    assert result["status"]=="available"
    assert result["source"]["transport"]=="official_csv" and result["source"]["fallback_used"] is False
    assert result["items"][0]["published_at"]=="2026-09-15T06:57:28+08:00"

def test_b08_name_match_with_wrong_code_fails_closed():
    result=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:CSV.replace("2330","9999",1),json_fetcher=lambda _: "[]")[0]
    assert result["status"]=="binding_failed" and result["items"]==[]

def test_c11_fallback_and_c12_source_failed():
    ok=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _: (_ for _ in ()).throw(OSError()),json_fetcher=lambda _:[{"公司代號":"2330","發言日期":"1150915","發言時間":"065728","主旨":"測試","說明":"內容"}])[0]
    assert ok["source"]["fallback_used"] is True and ok["source"]["transport"]=="official_json_openapi"
    failed=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _: "",json_fetcher=lambda _: "[]")[0]
    assert failed["status"]=="source_failed"

def test_c03_c04_and_b09_missing_multiple_and_conflict():
    missing=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:CSV.replace("2330","2317",1).replace("台積電","其他",1),json_fetcher=lambda _: "[]")[0]
    assert missing["status"]=="no_evidence_in_covered_scope" and missing["items"]==[]
    multi=CSV+"2330,台積電,1150914,090000,另一則,內容二\n"
    available=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:multi,json_fetcher=lambda _: "[]")[0]
    assert available["status"]=="available" and len(available["items"])==2
    conflict=CSV+"2330,台積電,1150915,65728,測試,不同內容\n"
    failed=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:conflict,json_fetcher=lambda _: "[]")[0]
    assert failed["status"]=="binding_failed" and failed["diagnostics"]

def test_c05_c06_revision_unresolved_and_future_fact_date():
    payload=CSV.replace("說明", "事實發生日,說明").replace("內容", "1150916,內容")
    result=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:payload,json_fetcher=lambda _: "[]")[0]
    item=result["items"][0]
    assert item["source_fact_date"]=="2026-09-16"
    assert item["revision_relation"]["status"]=="unresolved"

def test_internal_operation_evidence_schema_validates_target_bounded_result():
    result=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:CSV,json_fetcher=lambda _: "[]")[0]
    schema=json.loads((Path(__file__).resolve().parents[2] / "schemas/phase_g_material_disclosure_operation_evidence.v1.schema.json").read_text())
    jsonschema.validate(result,schema)

def test_c10_primary_csv_success_never_calls_json_fallback():
    calls=[]
    result=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:CSV,json_fetcher=lambda _: calls.append("json"))[0]
    assert result["status"]=="available" and calls==[]

def test_c13_c14_invalid_required_fields_and_empty_source_fail_closed():
    malformed="公司代號,公司名稱,發言日期,主旨,說明\n2330,台積電,1150915,測試,內容\n"
    invalid=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:malformed,json_fetcher=lambda _: "[]")[0]
    assert invalid["status"]=="source_failed"
    empty=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:"",json_fetcher=lambda _: "[]")[0]
    assert empty["status"]=="source_failed"

def test_c02_tpex_uses_its_own_official_contract():
    target={**TARGET,"canonical_target_id":"TPEX:6488","market":"TPEX","security_code":"6488"}
    payload=CSV.replace("2330","6488",1)
    result=execute([target],"TPEX",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:payload,json_fetcher=lambda _: "[]")[0]
    assert result["status"]=="available" and result["source"]["source_contract_id"]=="t187ap04_O"

def test_c08_source_report_date_is_source_faithful():
    payload=CSV.replace("公司代號,", "出表日期,公司代號,").replace("2330,", "1150916,2330,", 1)
    result=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:payload,json_fetcher=lambda _: "[]")[0]
    assert result["coverage"]["source_report_date"]=="2026-09-16"

def test_c15_c16_only_target_rows_are_retained_with_full_internal_description():
    long_text="x"*9000
    payload=CSV.replace("內容",long_text).replace("\n", "\n2317,其他,1150915,080000,無關,不保留\n", 1)
    result=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:payload,json_fetcher=lambda _: "[]")[0]
    assert len(result["items"])==1 and result["items"][0]["description_raw"]==long_text

def test_c09_never_fabricates_daily_refresh_clock():
    result=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:CSV,json_fetcher=lambda _: "[]")[0]
    assert "refresh" not in result["coverage"] and result["coverage"]["coverage_through"]=="2026-09-15"

def test_b3_real_shape_tpex_json_fallback_binds_date_and_code():
    target={**TARGET,"canonical_target_id":"TPEX:6488","market":"TPEX","security_code":"6488"}
    row={"Date":"1150916","SecuritiesCompanyCode":"6488","CompanyName":"測試公司","發言日期":"1150915","發言時間":"065728","主旨":"公告","符合條款":"1","事實發生日":"1150914","說明":"官方內容"}
    result=execute([target],"TPEX",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:(_ for _ in ()).throw(OSError()),json_fetcher=lambda _:[row])[0]
    assert result["status"]=="available" and result["source"]["transport"]=="official_json_openapi"
    assert result["coverage"]["source_report_date"]=="2026-09-16" and result["items"][0]["subject"]=="公告"

def test_b3_g1_hash_tie_break_is_ascending():
    payload=CSV+"2330,台積電,1150915,65728,另一則,內容二\n"
    result=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:payload,json_fetcher=lambda _:"[]")[0]
    assert [x["normalized_record_hash"] for x in result["items"]]==sorted(x["normalized_record_hash"] for x in result["items"])

def test_b3_g1_missing_contract_field_and_market_mismatch_fail_closed_before_binding():
    missing=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:CSV.replace("公司代號","代號"),json_fetcher=lambda _:"[]")[0]
    assert missing["status"]=="source_failed"
    mismatch=execute([{**TARGET,"market":"TPEX"}],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:(_ for _ in ()).throw(AssertionError()),json_fetcher=lambda _:(_ for _ in ()).throw(AssertionError()))[0]
    assert mismatch["status"]=="binding_failed" and mismatch["caveats"]==["route_target_market_mismatch"]

def test_b3_total_fallback_failure_retains_attempt_provenance():
    result=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:(_ for _ in ()).throw(OSError()),json_fetcher=lambda _:(_ for _ in ()).throw(ValueError()))[0]
    assert result["status"]=="source_failed" and result["source"]["fallback_attempted"] is True
    assert [x["transport"] for x in result["source"]["attempt_failures"]]==["official_csv","official_json_openapi"]

def test_b3_g1_schema_rejects_extra_target_and_inconsistent_status():
    result=execute([TARGET],"TWSE",observed_at="2026-09-16T00:00:00Z",csv_fetcher=lambda _:CSV,json_fetcher=lambda _:"[]")[0]
    schema=json.loads((Path(__file__).resolve().parents[2] / "schemas/phase_g_material_disclosure_operation_evidence.v1.schema.json").read_text())
    bad=json.loads(json.dumps(result)); bad["target"]["issuer_id"]="forbidden"
    with __import__('pytest').raises(jsonschema.ValidationError): jsonschema.validate(bad,schema,format_checker=jsonschema.FormatChecker())
    bad=json.loads(json.dumps(result)); bad["status"]="no_evidence_in_covered_scope"
    with __import__('pytest').raises(jsonschema.ValidationError): jsonschema.validate(bad,schema,format_checker=jsonschema.FormatChecker())
