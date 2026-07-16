#!/usr/bin/env python3
"""Run structural, schema, parser, classifier, lifecycle, and probe regression checks."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from classifier import classify_all, classify_record, merge_records, resolve
from common import isin_checksum_valid, normalize_date
from isin_parser import parse_html
from lifecycle_common import LifecycleSchemaDrift, detect_calendar
from merge_lifecycle_events import merge as merge_events
from parse_etn_termination import parse as parse_etn
from parse_tpex_announcement import parse as parse_tpex_announcement
from parse_tpex_delisted import parse as parse_tpex_delisted
from parse_twse_delisted import parse as parse_twse_delisted
from probe_sources import RedirectRejected, SafeRedirectHandler, assess_json, validate_url
from schema_validation import validate as validate_schema


ROOT = Path(__file__).resolve().parent.parent


class Validation:
    def __init__(self) -> None: self.checks: list[dict[str, object]] = []
    def check(self, condition: bool, name: str, detail: object = None) -> None:
        self.checks.append({"name": name, "passed": bool(condition), **({"detail": detail} if detail is not None else {})})
    def equal(self, actual: object, expected: object, name: str) -> None:
        self.check(actual == expected, name, {"actual": actual, "expected": expected} if actual != expected else None)
    def schema(self, instance: object, schema: dict, name: str) -> None:
        errors = validate_schema(instance, schema)
        self.check(not errors, name, errors[:10] if errors else None)


def main() -> int:
    v = Validation()
    required = [
        "SKILL.md", "agents/openai.yaml", "references/source-manifest.json", "references/source-contract.md",
        "references/classification-contract.md", "references/lifecycle-contract.md", "references/output-contract.md",
        "references/fixtures/official_observations.json", "scripts/common.py", "scripts/isin_parser.py",
        "scripts/classifier.py", "scripts/probe_sources.py", "scripts/schema_validation.py", "scripts/lifecycle_common.py",
        "scripts/parse_twse_delisted.py", "scripts/parse_tpex_delisted.py", "scripts/parse_tpex_announcement.py",
        "scripts/parse_etn_termination.py", "scripts/merge_lifecycle_events.py",
    ]
    schema_names = ["normalized-security-record", "classification-result", "resolution-result", "batch-classification-report", "lifecycle-event", "source-manifest", "probe-result"]
    required += [f"references/schemas/{name}.schema.json" for name in schema_names]
    for relative in required: v.check((ROOT / relative).is_file(), f"required_file:{relative}")

    schemas = {name: json.loads((ROOT / f"references/schemas/{name}.schema.json").read_text(encoding="utf-8")) for name in schema_names}
    for name, schema in schemas.items():
        v.equal(schema.get("$schema"), "https://json-schema.org/draft/2020-12/schema", f"schema_draft:{name}")

    manifest = json.loads((ROOT / "references/source-manifest.json").read_text(encoding="utf-8"))
    v.schema(manifest, schemas["source-manifest"], "schema:source_manifest")
    modes = manifest["identity_sources"]["twse_isin"]["modes"]
    v.equal([item["mode"] for item in modes], list(range(1, 13)), "manifest_has_modes_1_to_12")
    allowed = set(manifest["allowed_hosts"])
    datasets = manifest["twse_openapi"]["datasets"] + manifest["tpex_openapi"]["datasets"]
    for dataset in datasets:
        if dataset.get("url", "").endswith("swagger.json"): continue
        v.check(bool(dataset.get("payload_contract")), f"payload_contract:{dataset['id']}")

    def visit(value: object) -> None:
        if isinstance(value, dict):
            for child in value.values(): visit(child)
        elif isinstance(value, list):
            for child in value: visit(child)
        elif isinstance(value, str) and value.startswith("http"):
            parsed = urlparse(value.replace("{mode}", "1")); v.check(parsed.scheme == "https" and parsed.hostname in allowed, f"official_url:{value}")
    visit(manifest)

    fixtures = ROOT / "references/fixtures"
    fixture_specs = {
        "isin_mode1_zh_excerpt.html": (1, ["common_share", "preferred_share"]),
        "isin_mode2_mixed_excerpt.html": (2, ["common_share", "etf", "etn", "depositary_receipt", "warrant"]),
        "isin_mode3_bond_excerpt.html": (3, ["bond"]),
        "isin_mode4_mixed_excerpt.html": (4, ["common_share", "etf", "warrant"]),
        "isin_mode6_derivatives_excerpt.html": (6, ["future", "option"]),
        "isin_mode7_fund_excerpt.html": (7, ["fund"]),
        "isin_mode12_sto_excerpt.html": (12, ["security_token_debt", "security_token_equity", "security_token_unknown"]),
    }
    for filename, (mode, expected_types) in fixture_specs.items():
        parsed = parse_html((fixtures / filename).read_bytes(), lane="zh", mode=mode, source_url=f"https://isin.twse.com.tw/isin/C_public.jsp?strMode={mode}")
        v.equal(parsed["acquisition_status"], "data", f"parse:{filename}")
        actual_types = [classify_record(record)["instrument_type"] for record in parsed["records"]]
        v.equal(actual_types, expected_types, f"parser_sections:{filename}")
        for record in parsed["records"]: v.check(bool(record.get("section_heading")) or mode == 1 and record["security_code"] == "1111", f"section_preserved:{filename}:{record['security_code']}")

    en = parse_html((fixtures / "isin_mode1_en_excerpt.html").read_bytes(), lane="en", mode=1, source_url="https://isin.twse.com.tw/isin/e_C_public.jsp?strMode=1")
    blocked = parse_html((fixtures / "security_block.html").read_bytes(), lane="zh", mode=1, source_url="https://isin.twse.com.tw/isin/C_public.jsp?strMode=1")
    v.equal(en["acquisition_status"], "data", "parse_en_fixture")
    v.equal(blocked["acquisition_status"], "security_block", "detect_security_block")

    observations = json.loads((fixtures / "official_observations.json").read_text(encoding="utf-8"))
    records = observations["records"]
    for record in records:
        v.schema(record, schemas["normalized-security-record"], f"schema:normalized:{record['security_code']}:{record['source_lane']}")
        if record.get("isin"): v.check(isin_checksum_valid(record["isin"]), f"isin_checksum:{record['isin']}")
    for event in observations["events"]: v.schema(event, schemas["lifecycle-event"], f"schema:fixture_event:{event['security_code']}")

    merged = merge_records(records); by_code = {record.get("security_code"): record for record in merged}
    cases = {
        "1111": ("common_share", "public_unlisted", False, "confirmed_dual_lane"),
        "2364A": ("preferred_share", "public_unlisted", False, "confirmed_official_single_lane"),
        "AU9901": ("gold_spot", "tpex_gold_spot", False, "confirmed_official_single_lane"),
        "ST001D": ("security_token_debt", "sto_registry", False, "confirmed_official_single_lane"),
        "1240": ("issuer_record", "unknown", False, "confirmed_official_single_lane"),
    }
    for code, expected in cases.items():
        result = classify_record(by_code[code]); actual = (result["instrument_type"], result["market"], result["listed_common_stock_core_flag"], result["classification_status"])
        v.equal(actual, expected, f"classify:{code}")
        v.equal(result["cfi_mapping_scope"], "partial_controlled_prefixes_not_full_iso_10962", f"cfi_scope:{code}")

    context = {key: observations[key] for key in ("fixture_version", "observed_at")}
    batch = classify_all(records, context); v.schema(batch, schemas["batch-classification-report"], "schema:batch")
    v.equal(batch["record_count"], len(batch["records"]), "batch_count_matches")
    for index, record in enumerate(batch["records"]):
        v.schema(record, schemas["classification-result"], f"schema:classification:{index}")
        v.equal(record["observation"]["status"], "fixture_observation_only", f"fixture_provenance:{index}")
    for query, expected_status in (("1111", "resolved_exact_code"), ("欣欣水泥", "resolved_exact_name"), ("TW0001111003", "resolved_exact_isin")):
        result = resolve(records, query, context); v.equal(result["resolution_status"], expected_status, f"resolve:{query}")
        v.schema(result, schemas["resolution-result"], f"schema:resolution:{query}")
        for candidate in result["candidates"]: v.schema(candidate, schemas["classification-result"], f"schema:resolution_candidate:{query}")

    synthetic = [
        ({"source_lane":"zh","str_mode":2,"section_heading":"普通股","cfi":"ESVUFR"}, "common_share", True, "confirmed_official_single_lane"),
        ({"source_lane":"zh","str_mode":2,"section_heading":"ETF","cfi":"CEOGDU"}, "etf", False, "confirmed_official_single_lane"),
        ({"source_lane":"zh","str_mode":4,"section_heading":"認購(售)權證","cfi":"RWXXXX"}, "warrant", False, "confirmed_official_single_lane"),
        ({"source_lane":"zh","str_mode":2,"section_heading":"普通股","cfi":"EPNRCR"}, "common_share", False, "quarantine_conflict"),
    ]
    for index, (record, expected_type, expected_core, expected_status) in enumerate(synthetic, 1):
        result=classify_record(record); v.equal((result["instrument_type"],result["listed_common_stock_core_flag"],result["classification_status"]),(expected_type,expected_core,expected_status),f"synthetic:{index}")

    lagged = merge_records([
        {"isin":"TW0001101004","security_code":"1101","cfi":"ESVUFR","str_mode":2,"listing_date":"1962-02-09","source_lane":"zh","source_updated_date":"2026-07-15"},
        {"isin":"TW0001101004","security_code":"1101","cfi":"ESVUFR","str_mode":2,"listing_date":"1962-02-10","source_lane":"en","source_updated_date":"2026-07-14"},
    ])[0]
    v.equal(lagged["conflicts"][0]["category"], "observation_lag", "conflict_tier:observation_lag")
    v.check(classify_record(lagged)["classification_status"] != "quarantine_conflict", "date_lag_not_hard_quarantine")

    lifecycle_groups = [
        parse_twse_delisted((fixtures/"twse_delisted_excerpt.html").read_bytes(), "https://www.twse.com.tw/company/suspendListingCsvAndHtml?lang=zh&type=html"),
        parse_tpex_delisted((fixtures/"tpex_delisted_excerpt.html").read_bytes(), "https://www.tpex.org.tw/zh-tw/mainboard/listed/delisted.html"),
        parse_tpex_announcement((fixtures/"tpex_announcement_excerpt.html").read_bytes(), "https://www.tpex.org.tw/zh-tw/announce/market/announce.html", "emerging_terminated"),
        parse_etn((fixtures/"etn_termination_excerpt.html").read_bytes(), "https://www.twse.com.tw/zh/products/securities/etn/products/expire.html", "twse"),
    ]
    v.equal([len(group) for group in lifecycle_groups], [3,1,1,3], "lifecycle_adapters_parse")
    twse_by_code={event["security_code"]:event for event in lifecycle_groups[0]}
    v.equal(twse_by_code["2888"]["effective_date"], "2025-07-24", "twse_real_header_effective_date")
    v.equal(twse_by_code["2888"]["date_raw"], "114年07月24日", "twse_real_header_date_raw")
    v.equal(twse_by_code["2888"]["calendar"], "ROC", "twse_real_header_calendar")
    v.equal(lifecycle_groups[2][0]["effective_date"], "unknown", "announcement_not_effective_date")
    v.equal(lifecycle_groups[2][0]["announcement_date"], "2026-03-30", "announcement_date_preserved")
    for group in lifecycle_groups:
        for event in group: v.schema(event, schemas["lifecycle-event"], f"schema:adapter_event:{event['security_code']}")
    lifecycle_report = merge_events(lifecycle_groups); v.equal(lifecycle_report["event_count"], 8, "merge_lifecycle_events")
    try:
        parse_twse_delisted((fixtures/"lifecycle_unrecognized_header.html").read_bytes(), "https://www.twse.com.tw/company/suspendListingCsvAndHtml?lang=zh&type=html"); schema_drift_raised=False
    except LifecycleSchemaDrift as exc:
        schema_drift_raised=exc.issue_code == "unrecognized_lifecycle_header"
    v.check(schema_drift_raised,"lifecycle_unrecognized_header_not_silent_empty")
    failed_cli=subprocess.run([
        sys.executable,str(ROOT/"scripts/parse_twse_delisted.py"),str(fixtures/"lifecycle_unrecognized_header.html"),
        "--source-url","https://www.twse.com.tw/company/suspendListingCsvAndHtml?lang=zh&type=html"
    ],capture_output=True,text=True,check=False)
    v.equal(failed_cli.returncode,1,"lifecycle_schema_drift_nonzero_exit")
    failed_payload=json.loads(failed_cli.stdout)
    v.equal((failed_payload["acquisition_status"],failed_payload["event_count"],failed_payload["issues"][0]["code"]),("schema_drift",0,"unrecognized_lifecycle_header"),"lifecycle_schema_drift_structured_output")

    contract={"expected_json_type":"array","required_fields_any":["SecurityCode"],"minimum_record_count":1,"error_signatures":["error","maintenance"]}
    v.equal(assess_json(b'[{"SecurityCode":"1101"}]',contract)["acquisition_status"],"data","probe_semantic_data")
    v.equal(assess_json(b'{"error":"rate limit"}',contract)["acquisition_status"],"semantic_error","probe_reject_error_json")
    v.equal(assess_json(b'[]',contract)["semantic_data_present"],False,"probe_reject_empty_array")
    try:
        validate_url("https://evil.example/", list(allowed)); redirect_rejected=False
    except ValueError: redirect_rejected=True
    v.check(redirect_rejected,"redirect_final_host_allowlist")
    handler=SafeRedirectHandler(list(allowed)); request=urllib.request.Request("https://www.twse.com.tw/start")
    try:
        handler.redirect_request(request,None,302,"Found",{},"https://evil.example/target"); handler_rejected=False
    except RedirectRejected: handler_rejected=True
    v.check(handler_rejected,"redirect_handler_rejects_cross_host")
    probe_example={"requested_url":"https://www.tpex.org.tw/openapi/v1/test","final_url":"https://www.tpex.org.tw/openapi/v1/test","redirect_count":0,"observed_at":"2026-07-15T00:00:00+00:00","transport_success":True,"payload_parseable":True,"schema_valid":True,"semantic_data_present":True,"acquisition_status":"data","raw_payload_sha256":"0"*64}
    v.schema(probe_example,schemas["probe-result"],"schema:probe_result")

    for raw, expected in (("1150624","2026-06-24"),("114/10/01","2025-10-01"),("20251207","2025-12-07"),("115年3月30日","2026-03-30")):
        v.equal(normalize_date(raw),expected,f"date:{raw}")
    for raw, expected in (("114年07月24日","ROC"),("114/07/24","ROC"),("114-07-24","ROC"),("1140724","ROC"),("2025/07/24","Gregorian"),("20250724","Gregorian"),("unknown","unknown")):
        v.equal(detect_calendar(raw),expected,f"calendar:{raw}")

    failed=[item for item in v.checks if not item["passed"]]
    report={"status":"pass" if not failed else "fail","check_count":len(v.checks),"failed_count":len(failed),"failed":failed}
    print(json.dumps(report,ensure_ascii=False,indent=2)); return 0 if not failed else 1


if __name__ == "__main__": sys.exit(main())
