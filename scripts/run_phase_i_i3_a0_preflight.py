"""Offline A0 probe tooling, not an executor or A1 production contract.
Historical live authority is permanently disarmed. Unresolved mapping blocks
formal analysis; hypothetical test mappings never become committed authority.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
if not __debug__:
    raise RuntimeError("optimized_governance_execution_not_supported")
sys.path.insert(0, str(ROOT))
from scripts.m8r_filesystem_safety import atomic_write_bytes

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
P0_AUTHORITY = "USER_CHAT_2026-10-01_PHASE_I_I3_A0_P0_OFFLINE_PROBE_HARNESS_CLOSURE_AUTHORIZATION"
HISTORICAL_SHA = "43ef038ffd33a455ae52eff18a8f08e52436164b6d27d6140090b368810df5e0"
DEFAULT_MAPPING_AUTHORITY = ROOT / "docs/governance/phase_i/PHASE_I_I3_A0_CASH_INSTITUTIONAL_FLOW_PROBE_MAPPING_V1.json"
MAPPING_SHA = "e3af3d8b5ce11fe88f0c32efa45400126fe1991ec0c0725fbc3f480e2888638c"
NOT_APPLICABLE = "NOT_APPLICABLE_SOURCE_DOES_NOT_EXPOSE_COMPONENT_SPLIT"


def deny_network(*args, **kwargs):
    raise RuntimeError("P0_external_network_forbidden")


def fixed_get(*args, **kwargs):
    # No transport delegate in P0, independent of Attempt 1 file existence.
    # Future authority must introduce a separately reviewed new attempt latch.
    raise ValueError("fresh_a0_rearm_not_authorized")


def run(authority, mappings=None):
    raise ValueError("fresh_a0_rearm_not_authorized")


def numeric(value):
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("missing_or_invalid_integer")
    text = str(value).strip()
    if not re.fullmatch(r"[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)", text):
        raise ValueError("missing_or_invalid_integer")
    return int(text.replace(",", ""))


def official_date(value, encoding=None):
    if not isinstance(value, str):
        raise ValueError("unknown_official_date_encoding")
    if encoding in (None, "ROC_YYYMMDD") and re.fullmatch(r"[0-9]{7}", value):
        return date(int(value[:3]) + 1911, int(value[3:5]), int(value[5:])).isoformat()
    if encoding in (None, "Gregorian_YYYYMMDD") and re.fullmatch(r"[0-9]{8}", value):
        return date(int(value[:4]), int(value[4:6]), int(value[6:])).isoformat()
    raise ValueError("unknown_official_date_encoding")


def validate_mapping(authority, *, require_resolved=False):
    if authority.get("schema_version") != "phase_i_i3_a0_cash_institutional_flow_probe_mapping.v1":
        raise ValueError("mapping_schema")
    if authority.get("authority_scope") != "OFFLINE_PROBE_TOOLING_ONLY_NOT_A1_CONTRACT":
        raise ValueError("mapping_scope")
    markets = authority.get("markets", {})
    if set(markets) != {"TWSE", "TPEX"}:
        raise ValueError("mapping_markets")
    for market, m in markets.items():
        expected = ("證券代號", "date", "top_level", "Gregorian_YYYYMMDD") if market == "TWSE" else (
            "SecuritiesCompanyCode", "Date", "row", "ROC_YYYMMDD")
        if tuple(m.get(k) for k in ("code_field", "date_field", "date_source", "date_encoding")) != expected:
            raise ValueError("mapping_identity_date")
        if m.get("unit") != "share" or m.get("single_date_required") is not True:
            raise ValueError("mapping_unit_date_policy")
        core = m.get("required_common_core", {})
        if set(core) != {*CORE, "institutional_total_net_shares"}:
            raise ValueError("mapping_core")
        fields = []
        for group in CORE:
            if set(core[group]) != {"buy_shares", "sell_shares", "net_shares"}:
                raise ValueError("mapping_group")
            for name, keys in core[group].items():
                if keys is None:
                    if not (market == "TPEX" and group == "dealer_total" and name == "sell_shares"
                            and m["mapping_status"] == "UNRESOLVED"):
                        raise ValueError("unjustified_unresolved_mapping")
                    continue
                if not isinstance(keys, list) or not keys or not all(isinstance(k, str) and k for k in keys):
                    raise ValueError("mapping_expression")
                fields.extend(keys)
        total = core["institutional_total_net_shares"]
        if not isinstance(total, list) or not total or not all(isinstance(k, str) and k for k in total):
            raise ValueError("mapping_total")
        fields.extend(total)
        if len(set(fields)) != len(fields):
            raise ValueError("duplicate_common_core_assignment")
        optional = m.get("source_native_optional")
        split = m.get("conditional_invariants", {}).get("dealer_component_split")
        if not isinstance(optional, dict) or split not in ([], ["dealer_proprietary", "dealer_hedging"]):
            raise ValueError("mapping_optional_conditional")
        if any(g not in optional for g in split):
            raise ValueError("mapping_component_groups")
        for g, spec in optional.items():
            if isinstance(spec, str) and spec:
                continue
            if not isinstance(spec, dict) or set(spec) != {"buy_shares", "sell_shares", "net_shares"}:
                raise ValueError("mapping_optional_group")
            if not all(isinstance(keys, list) and keys and all(isinstance(k, str) and k for k in keys) for keys in spec.values()):
                raise ValueError("mapping_optional_expression")
    if require_resolved and (authority.get("mapping_status") == "UNRESOLVED"
                            or any(m["mapping_status"] == "UNRESOLVED" for m in markets.values())):
        raise ValueError("mapping_unresolved_dealer_total_sell")
    return authority


def load_mapping(path=DEFAULT_MAPPING_AUTHORITY):
    if Path(path).resolve() != DEFAULT_MAPPING_AUTHORITY.resolve():
        raise ValueError("unreviewed_mapping_path")
    body = DEFAULT_MAPPING_AUTHORITY.read_bytes()
    if hashlib.sha256(body).hexdigest() != MAPPING_SHA:
        raise ValueError("unreviewed_mapping_hash")
    return validate_mapping(json.loads(body))


def decode_payload(payload):
    if isinstance(payload, bytes):
        if len(payload) > MAX_BYTES:
            raise ValueError("payload_bound")
        def unique_pairs(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("duplicate_json_key")
                result[key] = value
            return result
        return json.loads(payload.decode("utf-8-sig"), object_pairs_hook=unique_pairs)
    return payload


def unpack(market, payload):
    if market == "TWSE":
        if not isinstance(payload, dict) or not isinstance(payload.get("fields"), list) or not isinstance(payload.get("data"), list):
            raise ValueError("unexpected_twse_root_shape")
        fields = payload["fields"]
        if not all(isinstance(f, str) for f in fields) or len(set(fields)) != len(fields):
            raise ValueError("duplicate_or_invalid_field_labels")
        rows = []
        for row in payload["data"]:
            if not isinstance(row, list) or len(row) != len(fields):
                raise ValueError("twse_row_width")
            rows.append(dict(zip(fields, row)))
        return fields, rows
    if market != "TPEX" or not isinstance(payload, list) or not all(isinstance(row, dict) for row in payload):
        raise ValueError("unexpected_tpex_root_shape")
    return sorted({key for row in payload for key in row}), payload


def expression(row, keys):
    if keys is None:
        raise ValueError("mapping_unresolved_dealer_total_sell")
    return sum(numeric(row[key]) for key in keys)


def group_values(row, fields):
    result = {name: expression(row, keys) for name, keys in fields.items()}
    if result["buy_shares"] < 0 or result["sell_shares"] < 0:
        raise ValueError("negative_buy_sell")
    return result


def normalized(row, mapping):
    core = mapping["required_common_core"]
    required = {g: group_values(row, core[g]) for g in CORE}
    required["institutional_total_net_shares"] = expression(row, core["institutional_total_net_shares"])
    optional = {}
    for group, fields in mapping["source_native_optional"].items():
        if isinstance(fields, str):
            if fields in row:
                optional[group] = row[fields]
        elif all(k in row for keys in fields.values() for k in keys):
            optional[group] = group_values(row, fields)
    return {"common_core": required, "source_native_optional": optional}


def arithmetic(rows, mapping):
    checks = {name: {"status": "PASS", "rows_checked": 0, "rows_passed": 0,
                     "rows_failed": 0, "missing_field_rows": 0, "first_failure_reason": None}
              for name in CORE + ["institutional_total_net", "dealer_component_net"]}
    split = mapping["conditional_invariants"]["dealer_component_split"]
    for row in rows:
        for name, check in checks.items():
            if name == "dealer_component_net":
                optional = mapping["source_native_optional"]
                if not split or not all(k in row for g in split for keys in optional[g].values() for k in keys):
                    continue
            check["rows_checked"] += 1
            try:
                core = mapping["required_common_core"]
                if name in CORE:
                    item = group_values(row, core[name])
                    valid = item["net_shares"] == item["buy_shares"] - item["sell_shares"]
                elif name == "institutional_total_net":
                    valid = expression(row, core["institutional_total_net_shares"]) == sum(
                        expression(row, core[g]["net_shares"]) for g in CORE)
                else:
                    components = [group_values(row, mapping["source_native_optional"][g]) for g in split]
                    dealer = group_values(row, core["dealer_total"])
                    valid = all(dealer[k] == sum(c[k] for c in components) for k in dealer)
                if not valid:
                    raise ValueError("arithmetic_inconsistency")
                check["rows_passed"] += 1
            except (ValueError, KeyError) as error:
                check["status"] = "FAIL"
                check["rows_failed"] += 1
                if isinstance(error, KeyError):
                    check["missing_field_rows"] += 1
                if check["first_failure_reason"] is None:
                    check["first_failure_reason"] = str(error)
    if checks["dealer_component_net"]["rows_checked"] == 0:
        checks["dealer_component_net"]["status"] = NOT_APPLICABLE
    return checks


def analyze_market(market, payload, mapping):
    # Pure helper for reviewed mappings OR explicitly hypothetical unit tests.
    payload = decode_payload(payload)
    fields, rows = unpack(market, payload)
    if not rows or mapping["code_field"] not in fields:
        raise ValueError("required_code_field_absent")
    matches = [row for row in rows if row.get(mapping["code_field"]) == TARGETS[market]]
    if len(matches) != 1:
        raise ValueError("target_binding_failed")
    raw_dates = ([payload[mapping["date_field"]]] if mapping["date_source"] == "top_level"
                 else [row[mapping["date_field"]] for row in rows])
    dates = sorted({official_date(d, mapping["date_encoding"]) for d in raw_dates})
    if mapping["single_date_required"] and len(dates) != 1:
        raise ValueError("unexpected_multiple_source_dates")
    observations = [normalized(row, mapping) for row in rows]
    checks = arithmetic(rows, mapping)
    return {"market": market, "exact_matches": 1, "row_count": len(rows), "field_count": len(fields),
            "normalized_trade_dates": dates,
            "selected_observation": {"security_code": TARGETS[market], "trade_date": dates[0],
                                    "unit": "share", **observations[rows.index(matches[0])]},
            "arithmetic": checks,
            "status": "FAIL" if any(c["rows_failed"] for c in checks.values()) else "PASS"}


def analyze_acquired_payloads(twse_payload, tpex_payload, mapping_authority):
    # Pure analysis: validate the supplied authority's pinned serialization,
    # without loading a file, external cache, clock or transport.
    authority_bytes = (json.dumps(mapping_authority, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if hashlib.sha256(authority_bytes).hexdigest() != MAPPING_SHA:
        raise ValueError("unreviewed_mapping_authority")
    reviewed = mapping_authority
    validate_mapping(reviewed, require_resolved=True)
    sources = {m: analyze_market(m, p, reviewed["markets"][m])
               for m, p in (("TWSE", twse_payload), ("TPEX", tpex_payload))}
    return {"sources": sources, "status": "PASS" if all(s["status"] == "PASS" for s in sources.values()) else "HOLD",
            "trade_date_symmetry": "same" if sources["TWSE"]["normalized_trade_dates"] == sources["TPEX"]["normalized_trade_dates"] else "different",
            "field_symmetry_matrix": [{"group": g, "classification": "COMMON_CORE"} for g in ["identity", "trade_date", *CORE, "institutional_total_net_shares"]] +
                [{"group": g, "classification": "SOURCE_NATIVE_OPTIONAL"} for g in ["foreign_dealer", "foreign_including_dealer", "security_name"]] +
                [{"group": "dealer_proprietary_and_hedging", "classification": "NOT_EQUIVALENT"}],
            "per_target_network_request_required": False, "raw_payload_persistence": "NONE", "market_network_calls": 0}


def write_analysis(output_root, relative_path, result):
    if Path(relative_path).name == Path(RECORD).name:
        raise ValueError("historical_attempt_immutable")
    allowed = {"sources", "status", "trade_date_symmetry", "field_symmetry_matrix",
               "per_target_network_request_required", "raw_payload_persistence", "market_network_calls"}
    if set(result) - allowed:
        raise ValueError("unreviewed_output_fields")
    for market, summary in result.get("sources", {}).items():
        if market not in TARGETS or set(summary) != {"market", "exact_matches", "row_count", "field_count",
                                                   "normalized_trade_dates", "selected_observation",
                                                   "arithmetic", "status"}:
            raise ValueError("unreviewed_source_summary")
        observation = summary["selected_observation"]
        if set(observation) != {"security_code", "trade_date", "unit", "common_core", "source_native_optional"}:
            raise ValueError("unreviewed_observation")
        if set(observation["common_core"]) != {*CORE, "institutional_total_net_shares"}:
            raise ValueError("unreviewed_observation")
        for name, values in observation["common_core"].items():
            if name == "institutional_total_net_shares":
                if type(values) is not int:
                    raise ValueError("unreviewed_observation")
            elif (set(values) != {"buy_shares", "sell_shares", "net_shares"}
                  or not all(type(v) is int for v in values.values())):
                raise ValueError("unreviewed_observation")
        optional = observation["source_native_optional"]
        specs = load_mapping()["markets"][market]["source_native_optional"]
        if set(optional) - set(specs):
            raise ValueError("unreviewed_optional_observation")
        for name, values in optional.items():
            if isinstance(specs[name], str):
                if not isinstance(values, str) or len(values) > 128:
                    raise ValueError("unreviewed_optional_observation")
            elif (set(values) != {"buy_shares", "sell_shares", "net_shares"}
                  or not all(type(v) is int for v in values.values())):
                raise ValueError("unreviewed_optional_observation")
        if set(summary["arithmetic"]) != {*CORE, "institutional_total_net", "dealer_component_net"}:
            raise ValueError("unreviewed_arithmetic_summary")
        for check in summary["arithmetic"].values():
            if set(check) != {"status", "rows_checked", "rows_passed", "rows_failed",
                              "missing_field_rows", "first_failure_reason"}:
                raise ValueError("unreviewed_arithmetic_summary")
    atomic_write_bytes(Path(output_root), relative_path,
                       (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
                       allow_overwrite=False)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline only; live execution NOT re-armed")
    parser.add_argument("--mapping-file", type=Path, default=DEFAULT_MAPPING_AUTHORITY)
    parser.add_argument("--twse-fixture", type=Path)
    parser.add_argument("--tpex-fixture", type=Path)
    parser.add_argument("--owner-authorization-reference", default=P0_AUTHORITY)
    args = parser.parse_args(argv)
    if args.owner_authorization_reference != P0_AUTHORITY:
        raise ValueError("fresh_a0_rearm_not_authorized")
    with patch("socket.socket.connect", deny_network), patch("socket.create_connection", deny_network):
        mapping = load_mapping(args.mapping_file)
        validate_mapping(mapping, require_resolved=True)
        if args.twse_fixture is None or args.tpex_fixture is None:
            raise ValueError("offline_fixture_paths_required")
        result = analyze_acquired_payloads(args.twse_fixture.read_bytes(), args.tpex_fixture.read_bytes(), mapping)
        print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
