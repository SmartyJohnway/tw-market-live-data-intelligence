"""Explicit one-shot A0 research probe, not a runtime executor.

Bodies/whole-market rows remain in memory. Only bounded telemetry, inventory,
one exact target observation per market and aggregate checks are persisted.
An explicit reviewed local mapping must be supplied before any I/O.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone, date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if not __debug__:
    raise RuntimeError("optimized_governance_execution_not_supported")
sys.path.insert(0, str(ROOT))
from scripts.m8r_filesystem_safety import atomic_write_bytes
from scripts.m8r_06_01c2_mode_a_security_master_loader import load_active_mode_a_security_master

BASELINE = "dafa5999c63d34d55a4665c6534aa77477448d79"
AUTHORITY = "USER_CHAT_2026-10-01_PHASE_I_I3_A0_CASH_INSTITUTIONAL_FLOW_SOURCE_TIMING_SYMMETRY_PREFLIGHT_AUTHORIZATION"
BRANCH = "phase-i/i3-a0-cash-institutional-flow-preflight"
RECORD = "docs/governance/phase_i/PHASE_I_I3_A0_CASH_INSTITUTIONAL_FLOW_SOURCE_TIMING_SYMMETRY_PREFLIGHT_2026-10-01.json"
ENDPOINTS = {
    "TWSE": "https://www.twse.com.tw/rwd/zh/fund/T86?date=20260930&selectType=ALLBUT0999&response=json",
    "TPEX": "https://www.tpex.org.tw/openapi/v1/tpex_3insti_daily_trading",
}
TARGETS = {"TWSE": "1101", "TPEX": "5347"}
MAX_BYTES = 4 * 1024 * 1024
CORE = ["foreign_and_mainland_excluding_foreign_dealer", "investment_trust", "dealer_total"]
PROTECTED = [
    "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json",
    "docs/data_capabilities/m8r_05b_capability_to_executor_routing_matrix.v3.json",
    "docs/data_capabilities/phase_i_i1_source_authority.v1.json",
    "docs/data_capabilities/phase_i_i2_source_authority.v1.json",
    "config/m8r_06_03_executor_registry_metadata.json",
    "scripts/m8r_06_03_production_adapter.py",
    "schemas/unified_market_evidence_request.v3.schema.json",
    "schemas/unified_market_evidence_result.v3.schema.json",
    "schemas/unified_market_evidence_audit_package.v3.schema.json",
]


def stamp():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def persist(record, *, first=False):
    atomic_write_bytes(ROOT, RECORD, (json.dumps(record, ensure_ascii=False, indent=2) + "\n").encode(),
                       allow_overwrite=not first)


class RejectRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def fixed_get(market):
    request = urllib.request.Request(ENDPOINTS[market], method="GET", headers={"Accept": "application/json"})
    opener = urllib.request.build_opener(RejectRedirects())
    try:
        response = opener.open(request, timeout=30)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        body = response.read(MAX_BYTES + 1)
        status = getattr(response, "status", getattr(response, "code", None))
        mime = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
    return status, mime, body


def numeric(value):
    if isinstance(value, bool):
        raise ValueError("boolean_not_share_count")
    text = str(value).strip().replace(",", "")
    if not re.fullmatch(r"[+-]?[0-9]+", text):
        raise ValueError("missing_or_invalid_integer")
    return int(text)


def official_date(value):
    text = str(value).strip()
    if re.fullmatch(r"[0-9]{7}", text):
        return date(int(text[:3]) + 1911, int(text[3:5]), int(text[5:7])).isoformat()
    if re.fullmatch(r"[0-9]{8}", text):
        return date(int(text[:4]), int(text[4:6]), int(text[6:8])).isoformat()
    raise ValueError("unknown_official_date_encoding")


def unpack(market, payload):
    if market == "TWSE":
        if not isinstance(payload, dict) or not isinstance(payload.get("fields"), list) or not isinstance(payload.get("data"), list):
            raise ValueError("unexpected_twse_root_shape")
        fields = payload["fields"]
        if len(set(fields)) != len(fields):
            raise ValueError("duplicate_field_labels")
        rows = []
        for row in payload["data"]:
            if not isinstance(row, list) or len(row) != len(fields):
                raise ValueError("twse_row_width")
            rows.append(dict(zip(fields, row)))
        return fields, rows
    if not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        raise ValueError("unexpected_tpex_root_shape")
    return sorted({key for row in payload for key in row}), payload


def expression(row, keys):
    values = [numeric(row[key]) for key in keys]
    return sum(values)


def normalized(row, mapping):
    result = {}
    for group, fields in mapping["groups"].items():
        result[group] = {name: expression(row, keys) for name, keys in fields.items()}
        if any(result[group].get(name, 0) < 0 for name in ("buy_shares", "sell_shares")):
            raise ValueError("negative_buy_sell")
    result["institutional_total_net_shares"] = expression(row, mapping["total_net"])
    return result


def arithmetic(rows, mapping):
    checks = {name: {"rows_checked": 0, "rows_passed": 0, "rows_failed": 0,
                     "missing_field_rows": 0, "first_failure_reason": None}
              for name in CORE + ["dealer_component_net", "institutional_total_net"]}
    for row in rows:
        for name, check in checks.items():
            check["rows_checked"] += 1
            try:
                obs = normalized(row, mapping)
                if name in CORE:
                    item = obs[name]
                    valid = item["net_shares"] == item["buy_shares"] - item["sell_shares"]
                elif name == "dealer_component_net":
                    valid = obs["dealer_total"]["net_shares"] == obs["dealer_proprietary"]["net_shares"] + obs["dealer_hedging"]["net_shares"]
                else:
                    valid = obs["institutional_total_net_shares"] == sum(obs[group]["net_shares"] for group in CORE)
                if not valid:
                    raise ValueError("arithmetic_inconsistency")
                check["rows_passed"] += 1
            except (ValueError, KeyError) as error:
                check["rows_failed"] += 1
                if isinstance(error, KeyError) or str(error) == "missing_or_invalid_integer":
                    check["missing_field_rows"] += 1
                if check["first_failure_reason"] is None:
                    check["first_failure_reason"] = str(error)
    return checks


def preflight():
    assert subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip() == BASELINE
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip() == BASELINE
    assert subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip() == BRANCH
    assert not subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).strip()
    assert not subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=ROOT, text=True).strip()
    runtime = load_active_mode_a_security_master(security_master_root=ROOT / "data/security_master")
    assert runtime.validation["valid"]
    targets = []
    for market, code in TARGETS.items():
        target = runtime.lookup["by_canonical"][market + ":" + code]
        cls = target["classification"]
        assert (cls["market"], cls["instrument_family"], cls["instrument_type"], target["execution_eligibility"]["status"]) == (
            market, "company_share", "common_share", "allowed")
        targets.append({"canonical_target_id": target["canonical_target_id"], "market": market,
            "security_code": code, "isin": target["identity"]["isin"], "record_hash": target["record_hash"],
            "instrument_family": cls["instrument_family"], "instrument_type": cls["instrument_type"],
            "execution_eligibility": "allowed"})
    hashes = {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in PROTECTED}
    return {"pointer": runtime.pointer, "validation": runtime.validation, "targets": targets}, hashes


def run(authority, mappings):
    if authority != AUTHORITY:
        raise ValueError("owner_authority_required")
    if not isinstance(mappings, dict) or set(mappings) != set(ENDPOINTS):
        raise ValueError("offline_mapping_required_before_io")
    for mapping in mappings.values():
        if not isinstance(mapping, dict) or not {"code_field", "date_field", "groups", "total_net"} <= set(mapping):
            raise ValueError("reviewed_mapping_fields_required_before_io")
        if not set(CORE) <= set(mapping["groups"]):
            raise ValueError("common_core_mapping_required_before_io")
    identity, hashes = preflight()
    record = {"schema_version": "phase_i_i3_a0_cash_institutional_flow_source_timing_symmetry_preflight.v1",
        "owner_authority": AUTHORITY, "baseline_main": BASELINE, "branch": BRANCH, "probe_timestamp": stamp(),
        "network_budget": {"TWSE": 1, "TPEX": 1, "total": 2, "retry": 0, "timeout_seconds": 30, "maximum_probe_bytes": MAX_BYTES, "redirects": "rejected"},
        "actual_network_counts": {"TWSE": 0, "TPEX": 0, "other_market_data": 0}, "retry_count": 0,
        "security_master": identity, "production_authority_sha256": hashes, "sources": {},
        "status": "IN_PROGRESS", "a1_contract_freeze_authorized": False, "implementation_authorized": False,
        "production_activation_authorized": False, "merge_authorized": False, "i3_other_families_authorized": False}
    # Durable one-shot latch before any I/O; a second invocation cannot overwrite.
    persist(record, first=True)
    memory = {}
    for market in ENDPOINTS:
        info = {"endpoint": ENDPOINTS[market], "retrieved_at": stamp(), "get_count": 1}
        record["actual_network_counts"][market] = 1
        record["sources"][market] = info
        persist(record)
        try:
            status, mime, body = fixed_get(market)
            info.update(http_status=status, base_mime=mime, response_bytes=len(body),
                        response_sha256=hashlib.sha256(body).hexdigest(), redirect_outcome="rejected" if status in range(300, 400) else "none")
            if status != 200 or len(body) > MAX_BYTES:
                raise ValueError("transport_status_or_bound")
            payload = json.loads(body.decode("utf-8-sig"))
            fields, rows = unpack(market, payload)
            info.update(root_type=type(payload).__name__, top_level_keys=sorted(payload) if isinstance(payload, dict) else [],
                        fields=fields, field_count=len(fields), row_count=len(rows))
            memory[market] = (payload, rows)
            code_fields = [mappings[market]["code_field"]]
            if code_fields[0] not in fields:
                raise ValueError("reviewed_code_field_not_in_payload")
            matches = [(key, row) for key in code_fields for row in rows if str(row.get(key, "")).strip() == TARGETS[market]]
            info["binding_match_count"] = len(matches)
            print(json.dumps({"market": market, "inventory": info}, ensure_ascii=False), flush=True)
            if len(matches) == 1:
                key, selected = matches[0]
                info["exact_code_field"] = key
                # Discovery output only: one target's numeric observations, no raw row set.
                selected_numbers = {}
                for field, value in selected.items():
                    if field not in {key, "Date", "證券名稱", "名稱", "SecuritiesName", "SecurityName", "Name"}:
                        try: selected_numbers[field] = numeric(value)
                        except ValueError: pass
                print(json.dumps({"market": market, "fields": fields, "selected_numeric_observations": selected_numbers,
                                  "source_date": payload.get("date") if isinstance(payload, dict) else selected.get("Date")},
                                 ensure_ascii=False), flush=True)
        except Exception as error:
            info["error"] = type(error).__name__ + ":" + str(error)
        persist(record)
    try:
        for market, (payload, rows) in memory.items():
            mapping = mappings[market]
            info = record["sources"][market]
            selected = [row for row in rows if str(row.get(info["exact_code_field"], "")).strip() == TARGETS[market]]
            if len(selected) != 1:
                raise ValueError("target_binding_failed")
            dates = sorted({str(row[mapping["date_field"]]) for row in rows}) if market == "TPEX" else [str(payload[mapping["date_field"]])]
            normalized_dates = sorted({official_date(value) for value in dates})
            info.update(source_mapping=mapping, unique_source_dates=dates, normalized_trade_dates=normalized_dates,
                date_encoding="ROC compact YYYMMDD" if all(len(value) == 7 for value in dates) else "Gregorian YYYYMMDD",
                selected_observation={"market": market, "security_code": TARGETS[market],
                    "trade_date": official_date(selected[0][mapping["date_field"]]) if market == "TPEX" else official_date(dates[0]),
                    "unit": "share", **normalized(selected[0], mapping)}, arithmetic=arithmetic(rows, mapping),
                publication_phase_in_payload="absent",
                publication_timestamp_fields=[field for field in info["fields"] if any(token in field.lower() for token in ("timestamp", "publish", "update", "time"))])
        record["status"] = "PROBED_AWAITING_GOVERNANCE_REVIEW"
    except Exception as error:
        record["status"] = "HOLD"
        record["failure_reason"] = type(error).__name__ + ":" + str(error)
    record["raw_payload_persistence"] = "NONE"
    record["raw_payload_policy_proof"] = "No body or whole-market rows are written; only telemetry, inventory, exact-target normalized observations and aggregates. Bodies remain process-memory only."
    persist(record)
    print(json.dumps(record, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner-authorization-reference", required=True)
    parser.add_argument("--mapping-file", type=Path, required=True)
    args = parser.parse_args()
    # Historical A0 authorization is already consumed. The durable record latch
    # refuses another invocation; no CLI retry or stdin-dependent closure.
    run(args.owner_authorization_reference, json.loads(args.mapping_file.read_text(encoding="utf-8")))
