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
ADJUDICATION_AUTHORITY_PATH = ROOT / "docs/governance/phase_i/PHASE_I_I3_A0_TPEX_DEALER_SELL_ADJUDICATION_V1.json"
ADJUDICATION_AUTHORITY_SHA = "666108fdd187f3ec753acc2a258e3ea7bd9415cc371346b5f32dc231ea665240"
DEALER_SELL_CANDIDATES = ("Dealers-TotalSell", "Dealers -TotalSell")
TPEX_BUY_FIELD = "Dealers-TotalBuy"
TPEX_NET_FIELD = "Dealers-Difference"
TPEX_TOTAL_FIELD = "TotalDifference"
TPEX_FOREIGN_NET_FIELD = "Foreign Investors include Mainland Area Investors (Foreign Dealers excluded)-Difference"
TPEX_TRUST_NET_FIELD = "SecuritiesInvestmentTrustCompanies-Difference"
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


def load_adjudication_authority():
    body = ADJUDICATION_AUTHORITY_PATH.read_bytes()
    if hashlib.sha256(body).hexdigest() != ADJUDICATION_AUTHORITY_SHA:
        raise ValueError("unreviewed_adjudication_authority_hash")
    return json.loads(body)


def validate_adjudication_authority(authority):
    if not isinstance(authority, dict):
        raise ValueError("adjudication_authority_required")
    candidates = authority.get("candidate_sell_fields")
    expected_keys = {"schema_version", "authority_scope", "semantic_target", "buy_field", "net_field",
                     "candidate_sell_fields", "selection_mode", "official_semantic_basis",
                     "independent_institutional_total_invariant", "selection_status",
                     "network_calls_authorized", "synthetic_values_are_not_source_authority"}
    if set(authority) != expected_keys:
        raise ValueError("unreviewed_adjudication_authority")
    if (authority.get("schema_version") != "phase_i_i3_a0_tpex_dealer_sell_adjudication.v1"
            or authority.get("authority_scope") != "OFFLINE_CANDIDATE_KEY_ADJUDICATION_ONLY"
            or authority.get("semantic_target") != "dealer_total.sell_shares"
            or authority.get("selection_mode") != "UNIQUE_WHOLE_DATASET_ARITHMETIC_MATCH"
            or authority.get("buy_field") != TPEX_BUY_FIELD
            or authority.get("net_field") != TPEX_NET_FIELD
            or not isinstance(candidates, list)
            or len(candidates) != len(set(candidates))
            or set(candidates) != set(DEALER_SELL_CANDIDATES)
            or authority.get("selection_status") != "UNRESOLVED_UNTIL_FRESH_SOURCE"):
        raise ValueError("unreviewed_adjudication_authority")
    expected_basis = {
        "authority": "TPEx S35 official daily institutional trading semantic reference",
        "reference": "https://www.tpex.org.tw/web/stock/3insti/daily_trade/3itrade_hedge.php?l=zh-tw",
        "dealer_aggregate": ["buy shares", "sell shares", "net shares"],
        "dealer_proprietary": "separate optional detail",
        "dealer_hedging": "separate optional detail",
        "three_institution_total": "foreign/mainland excluding foreign dealer + investment trust + dealer aggregate",
        "key_selection_limit": "S35 semantic object establishes the aggregate concept and total formula; it does not identify either OpenAPI sell key.",
    }
    if (authority.get("official_semantic_basis") != expected_basis
            or authority.get("network_calls_authorized") != 0
            or authority.get("synthetic_values_are_not_source_authority") is not True):
        raise ValueError("adjudication_semantic_anchor")
    invariant = authority.get("independent_institutional_total_invariant", {})
    if invariant != {
        "total_field": TPEX_TOTAL_FIELD,
        "foreign_ex_dealer_net_field": TPEX_FOREIGN_NET_FIELD,
        "investment_trust_net_field": TPEX_TRUST_NET_FIELD,
        "dealer_net_field": TPEX_NET_FIELD,
        "rule": "TotalDifference == foreign_ex_dealer_net + investment_trust_net + Dealers-Difference for every source row.",
    }:
        raise ValueError("adjudication_invariant_authority")
    return authority


def _candidate_stats(rows, candidate):
    stats = {"candidate": candidate, "rows_checked": 0, "rows_passed": 0, "rows_failed": 0,
             "missing_rows": 0, "first_failure": None}
    if not rows:
        stats["first_failure"] = "zero_rows"
        return stats
    if any(candidate not in row for row in rows):
        stats["missing_rows"] = sum(candidate not in row for row in rows)
        stats["rows_failed"] = stats["missing_rows"]
        stats["first_failure"] = "candidate_field_absent"
    for index, row in enumerate(rows, start=1):
        if candidate not in row:
            continue
        stats["rows_checked"] += 1
        try:
            required = (TPEX_BUY_FIELD, candidate, TPEX_NET_FIELD)
            if any(key not in row for key in required):
                raise KeyError("required_field_absent")
            values = [row[key] for key in required]
            if any(isinstance(v, str) and v.strip().upper() in {"", "-", "NULL"} for v in values):
                stats["missing_rows"] += 1
                raise ValueError("missing_share_count")
            buy, sell, net = [numeric(value) for value in values]
            if buy < 0 or sell < 0:
                raise ValueError("negative_share_count")
            if buy - sell != net:
                raise ValueError("arithmetic_mismatch")
            stats["rows_passed"] += 1
        except KeyError as error:
            stats["missing_rows"] += 1
            stats["rows_failed"] += 1
            if stats["first_failure"] is None:
                stats["first_failure"] = f"row_{index}:missing_required_field"
        except ValueError as error:
            stats["rows_failed"] += 1
            reason = "missing_share_count" if str(error) == "missing_share_count" else (
                "malformed_integer" if str(error) == "missing_or_invalid_integer" else str(error))
            if stats["first_failure"] is None:
                stats["first_failure"] = f"row_{index}:{reason}"
    return stats


def _institutional_total_stats(rows):
    stats = {"rows_checked": 0, "rows_passed": 0, "rows_failed": 0,
             "missing_rows": 0, "first_failure": None}
    fields = (TPEX_TOTAL_FIELD, TPEX_FOREIGN_NET_FIELD, TPEX_TRUST_NET_FIELD, TPEX_NET_FIELD)
    if not rows:
        stats["first_failure"] = "zero_rows"
        return stats
    for index, row in enumerate(rows, start=1):
        stats["rows_checked"] += 1
        try:
            if any(key not in row for key in fields):
                missing = sum(key not in row for key in fields)
                stats["missing_rows"] += 1
                raise KeyError(f"missing_fields:{missing}")
            values = [row[key] for key in fields]
            if any(isinstance(v, str) and v.strip().upper() in {"", "-", "NULL"} for v in values):
                stats["missing_rows"] += 1
                raise ValueError("missing_share_count")
            total, foreign_net, trust_net, dealer_net = [numeric(value) for value in values]
            if total != foreign_net + trust_net + dealer_net:
                raise ValueError("institutional_total_mismatch")
            stats["rows_passed"] += 1
        except KeyError as error:
            stats["rows_failed"] += 1
            if stats["first_failure"] is None:
                stats["first_failure"] = f"row_{index}:missing_required_field"
        except ValueError as error:
            stats["rows_failed"] += 1
            reason = "missing_share_count" if str(error) == "missing_share_count" else (
                "malformed_integer" if str(error) == "missing_or_invalid_integer" else str(error))
            if stats["first_failure"] is None:
                stats["first_failure"] = f"row_{index}:{reason}"
    return stats


def adjudicate_tpex_dealer_sell(rows, authority):
    """Pure, order-independent candidate key selection over a whole payload."""
    validate_adjudication_authority(authority)
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("tpex_rows_must_be_mappings")
    statistics = {candidate: _candidate_stats(rows, candidate)
                  for candidate in sorted(authority["candidate_sell_fields"])}
    institutional = _institutional_total_stats(rows)
    qualifies = [candidate for candidate, stats in statistics.items()
                 if stats["rows_checked"] > 0 and stats["rows_failed"] == 0 and stats["missing_rows"] == 0]
    if any(stats["missing_rows"] for stats in statistics.values()):
        status, selected = "MISSING_CANDIDATE_FIELD", None
    elif not qualifies:
        status, selected = "NO_MATCH", None
    elif institutional["rows_checked"] == 0 or institutional["rows_failed"] or institutional["missing_rows"]:
        status = "INSTITUTIONAL_TOTAL_MISMATCH"
        selected = None
    elif len(qualifies) == 1:
        status, selected = "RESOLVED", qualifies[0]
    elif len(qualifies) > 1:
        status, selected = "AMBIGUOUS_ALIAS", None
    else:
        status, selected = "NO_MATCH", None
    return {"selection_status": status, "selected_candidate": selected,
            "candidate_fields": sorted(authority["candidate_sell_fields"]),
            "candidate_statistics": statistics,
            "institutional_total_invariant": institutional,
            "selection_reason": {
                "RESOLVED": "exactly_one_candidate_passed_all_rows_and_independent_total_invariant",
                "AMBIGUOUS_ALIAS": "multiple_candidates_passed_all_rows",
                "NO_MATCH": "no_candidate_passed_all_rows",
                "MISSING_CANDIDATE_FIELD": "candidate_field_or_value_missing_in_payload",
                "INSTITUTIONAL_TOTAL_MISMATCH": "independent_three_institution_total_invariant_failed",
            }[status]}


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


def analyze_acquired_payloads(twse_payload, tpex_payload, mapping_authority, adjudication_authority=None):
    # Pure analysis: validate the supplied authority's pinned serialization,
    # without loading a file, external cache, clock or transport.
    authority_bytes = (json.dumps(mapping_authority, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if hashlib.sha256(authority_bytes).hexdigest() != MAPPING_SHA:
        raise ValueError("unreviewed_mapping_authority")
    reviewed = mapping_authority
    validate_mapping(reviewed)
    adjudication = None
    tpex_mapping = reviewed["markets"]["TPEX"]
    if tpex_mapping["mapping_status"] == "UNRESOLVED":
        if adjudication_authority is None:
            raise ValueError("mapping_unresolved_dealer_total_sell")
        authority = validate_adjudication_authority(adjudication_authority)
        tpex_payload = decode_payload(tpex_payload)
        _, tpex_rows = unpack("TPEX", tpex_payload)
        adjudication = adjudicate_tpex_dealer_sell(tpex_rows, authority)
        if adjudication["selection_status"] != "RESOLVED":
            return {"sources": {}, "status": "HOLD",
                    "trade_date_symmetry": "NOT_EVALUATED",
                    "field_symmetry_matrix": [],
                    "dealer_sell_adjudication": adjudication,
                    "per_target_network_request_required": False,
                    "raw_payload_persistence": "NONE", "market_network_calls": 0}
        # Ephemeral, process-local resolution; never modify the committed P0 map.
        import copy
        reviewed = copy.deepcopy(reviewed)
        tpex_mapping = reviewed["markets"]["TPEX"]
        tpex_mapping["required_common_core"]["dealer_total"]["sell_shares"] = [adjudication["selected_candidate"]]
        tpex_mapping["mapping_status"] = "RESOLVED_BY_P1_WHOLE_DATASET_ARITHMETIC"
        tpex_mapping.pop("unresolved_fields", None)
        reviewed["mapping_status"] = "RESOLVED_EPHEMERAL"
        validate_mapping(reviewed, require_resolved=True)
    sources = {m: analyze_market(m, payload, reviewed["markets"][m])
               for m, payload in (("TWSE", twse_payload), ("TPEX", tpex_payload))}
    return {"sources": sources, "status": "PASS" if all(s["status"] == "PASS" for s in sources.values()) else "HOLD",
            "trade_date_symmetry": "same" if sources["TWSE"]["normalized_trade_dates"] == sources["TPEX"]["normalized_trade_dates"] else "different",
            "field_symmetry_matrix": [{"group": g, "classification": "COMMON_CORE"} for g in ["identity", "trade_date", *CORE, "institutional_total_net_shares"]] +
                [{"group": g, "classification": "SOURCE_NATIVE_OPTIONAL"} for g in ["foreign_dealer", "foreign_including_dealer", "security_name"]] +
                [{"group": "dealer_proprietary_and_hedging", "classification": "NOT_EQUIVALENT"}],
            "dealer_sell_adjudication": adjudication,
            "per_target_network_request_required": False, "raw_payload_persistence": "NONE", "market_network_calls": 0}


def write_analysis(output_root, relative_path, result):
    if Path(relative_path).name == Path(RECORD).name:
        raise ValueError("historical_attempt_immutable")
    allowed = {"sources", "status", "trade_date_symmetry", "field_symmetry_matrix", "dealer_sell_adjudication",
               "per_target_network_request_required", "raw_payload_persistence", "market_network_calls"}
    if set(result) - allowed:
        raise ValueError("unreviewed_output_fields")
    if (result.get("status") not in {"PASS", "HOLD"}
            or result.get("trade_date_symmetry") not in {"same", "different", "NOT_EVALUATED"}
            or result.get("per_target_network_request_required") is not False
            or result.get("raw_payload_persistence") != "NONE"
            or result.get("market_network_calls") != 0):
        raise ValueError("unreviewed_analysis_summary")
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
    adjudication = result.get("dealer_sell_adjudication")
    if adjudication is not None:
        if set(adjudication) != {"selection_status", "selected_candidate", "candidate_fields",
                                 "candidate_statistics", "institutional_total_invariant", "selection_reason"}:
            raise ValueError("unreviewed_adjudication_summary")
        if (adjudication["selection_status"] not in {"RESOLVED", "AMBIGUOUS_ALIAS", "NO_MATCH",
                "MISSING_CANDIDATE_FIELD", "INSTITUTIONAL_TOTAL_MISMATCH"}
                or adjudication["selected_candidate"] not in (None, *DEALER_SELL_CANDIDATES)
                or adjudication["candidate_fields"] != sorted(DEALER_SELL_CANDIDATES)
                or adjudication["selection_reason"] not in {
                    "exactly_one_candidate_passed_all_rows_and_independent_total_invariant",
                    "multiple_candidates_passed_all_rows", "no_candidate_passed_all_rows",
                    "candidate_field_or_value_missing_in_payload",
                    "independent_three_institution_total_invariant_failed"}):
            raise ValueError("unreviewed_adjudication_summary")
        if set(adjudication["candidate_statistics"]) != set(DEALER_SELL_CANDIDATES):
            raise ValueError("unreviewed_adjudication_summary")
        for candidate, stats in adjudication["candidate_statistics"].items():
            if stats["candidate"] != candidate or set(stats) != {"candidate", "rows_checked", "rows_passed",
                    "rows_failed", "missing_rows", "first_failure"}:
                raise ValueError("unreviewed_adjudication_summary")
            if stats["first_failure"] is not None and not re.fullmatch(
                    r"(?:zero_rows|candidate_field_absent|row_[0-9]+:(?:missing_required_field|missing_share_count|malformed_integer|negative_share_count|arithmetic_mismatch))",
                    stats["first_failure"]):
                raise ValueError("unreviewed_adjudication_summary")
            if not all(type(stats[k]) is int and stats[k] >= 0 for k in
                       ("rows_checked", "rows_passed", "rows_failed", "missing_rows")):
                raise ValueError("unreviewed_adjudication_summary")
        invariant = adjudication["institutional_total_invariant"]
        if set(invariant) != {"rows_checked", "rows_passed", "rows_failed", "missing_rows", "first_failure"}:
            raise ValueError("unreviewed_adjudication_summary")
        if not all(type(invariant[k]) is int and invariant[k] >= 0 for k in
                   ("rows_checked", "rows_passed", "rows_failed", "missing_rows")):
            raise ValueError("unreviewed_adjudication_summary")
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
        validate_mapping(mapping)
        if args.twse_fixture is None or args.tpex_fixture is None:
            raise ValueError("offline_fixture_paths_required")
        result = analyze_acquired_payloads(args.twse_fixture.read_bytes(), args.tpex_fixture.read_bytes(),
                                           mapping, load_adjudication_authority())
        print(json.dumps(result, ensure_ascii=True))


if __name__ == "__main__":
    main()
