"""Pure, injected-bytes-only I3-A2 source preparation and target projection.

No source transport, system clock, or historical A0 research runner is imported.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_REL = "docs/governance/phase_i/PHASE_I_I3_A1_CASH_INSTITUTIONAL_FLOW_SOURCE_EVIDENCE_CONTRACT_2026-10-03_FROZEN.json"
CONTRACT_SHA256 = "4f6c00f8c0ef61bd7c5c55daa81e23cf25ec6335c4fe99ef4c539572419f5428"
CONTRACT_OBJECT_SHA256 = "b8a9b5b24459e35a23852acc4866b6c18430db98b0adc46d0c0d98cdfc2df4b9"
EVIDENCE_SCHEMA = "cash_institutional_flow_context_evidence.v1"
MAX_BYTES = 4 * 1024 * 1024
CORE_GROUPS = ("foreign_and_mainland_excluding_foreign_dealer", "investment_trust", "dealer_total")


def load_frozen_contract() -> dict[str, Any]:
    body = (ROOT / CONTRACT_REL).read_bytes()
    if hashlib.sha256(body).hexdigest() != CONTRACT_SHA256:
        raise ValueError("frozen_a1_contract_hash_mismatch")
    contract = json.loads(body)
    if (contract.get("gate"), contract.get("status"), contract.get("capability_id")) != (
        "I3-A1", "FROZEN_PASS", "cash_institutional_flow_context"
    ):
        raise ValueError("frozen_a1_contract_identity_invalid")
    validate_frozen_contract_object(contract)
    return contract


def validate_frozen_contract_object(contract: dict[str, Any]) -> None:
    """Reject even process-local changes to the sealed A1 semantic object."""
    canonical = json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    if hashlib.sha256(canonical).hexdigest() != CONTRACT_OBJECT_SHA256:
        raise ValueError("frozen_a1_contract_object_mutated")


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _source_date(value: Any, encoding: str) -> str:
    if not isinstance(value, str):
        raise ValueError("source_date_invalid")
    if encoding == "Gregorian_YYYYMMDD" and re.fullmatch(r"[0-9]{8}", value):
        return date(int(value[:4]), int(value[4:6]), int(value[6:])).isoformat()
    if encoding == "ROC_YYYMMDD" and re.fullmatch(r"[0-9]{7}", value):
        return date(int(value[:3]) + 1911, int(value[3:5]), int(value[5:])).isoformat()
    raise ValueError("source_date_invalid")


def _integer(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("required_integer_invalid")
    text = str(value).strip()
    if not re.fullmatch(r"[+-]?(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)", text):
        raise ValueError("required_integer_invalid")
    return int(text.replace(",", ""))


def _expression(row: dict[str, Any], keys: list[str]) -> int:
    return sum(_integer(row[key]) for key in keys)


def _flow(row: dict[str, Any], mapping: dict[str, list[str]]) -> dict[str, int]:
    values = {name: _expression(row, keys) for name, keys in mapping.items()}
    if values["buy_shares"] < 0 or values["sell_shares"] < 0:
        raise ValueError("negative_buy_sell")
    if values["net_shares"] != values["buy_shares"] - values["sell_shares"]:
        raise ValueError("net_arithmetic_mismatch")
    return values


def _normalized_row(row: dict[str, Any], source: dict[str, Any], market: str) -> dict[str, Any]:
    mapping = source["required_common_core"]
    groups = {name: _flow(row, mapping[name]) for name in CORE_GROUPS}
    total = _expression(row, mapping["institutional_total_net_shares"])
    if total != sum(groups[name]["net_shares"] for name in CORE_GROUPS):
        raise ValueError("institutional_total_mismatch")
    optional: dict[str, Any] = {}
    for name, fields in source["source_native_optional"].items():
        if isinstance(fields, str):
            if fields in row:
                optional[name] = row[fields]
        elif all(key in row for keys in fields.values() for key in keys):
            optional[name] = _flow(row, fields)
    if market == "TWSE":
        if "dealer_proprietary" not in optional or "dealer_hedging" not in optional:
            raise ValueError("twse_dealer_components_missing")
        if any(groups["dealer_total"][field] != optional["dealer_proprietary"][field] + optional["dealer_hedging"][field]
               for field in ("buy_shares", "sell_shares", "net_shares")):
            raise ValueError("twse_dealer_components_mismatch")
    return {"foreign_and_mainland_excluding_foreign_dealer": groups["foreign_and_mainland_excluding_foreign_dealer"],
            "investment_trust": groups["investment_trust"], "dealer_total": groups["dealer_total"],
            "institutional_total_net_shares": total, "source_native_optional": optional}


@dataclass(frozen=True)
class PreparedSource:
    market: str
    trade_date: str | None
    index: dict[str, list[dict[str, Any]]]
    row_count: int
    field_count: int
    error_code: str | None


def prepare_market_source(market: str, payload: bytes, *, twse_governed_source_date: str | None,
                          contract: dict[str, Any]) -> PreparedSource:
    """Decode and validate every row exactly once; never persist source rows."""
    if market not in ("TWSE", "TPEX"):
        raise ValueError("unsupported_market")
    if market == "TWSE" and (not isinstance(twse_governed_source_date, str)
                             or not re.fullmatch(r"[0-9]{8}", twse_governed_source_date)):
        raise ValueError("explicit_twse_governed_source_date_required")
    if market == "TPEX" and twse_governed_source_date is not None:
        # The caller passes this shared argument for mixed batches; TPEx ignores it.
        pass
    if not isinstance(payload, bytes) or len(payload) > MAX_BYTES:
        return PreparedSource(market, None, {}, 0, 0, "source_payload_missing_or_oversized")
    source = contract["sources"][market]
    try:
        root = json.loads(payload.decode("utf-8-sig"), object_pairs_hook=_unique_pairs)
        if market == "TWSE":
            if not isinstance(root, dict) or not isinstance(root.get("fields"), list) or not isinstance(root.get("data"), list):
                raise ValueError("twse_root_invalid")
            fields = root["fields"]
            if not all(isinstance(x, str) for x in fields) or len(fields) != len(set(fields)):
                raise ValueError("twse_fields_invalid")
            rows = []
            for values in root["data"]:
                if not isinstance(values, list) or len(values) != len(fields):
                    raise ValueError("twse_row_width_invalid")
                rows.append(dict(zip(fields, values)))
            if root.get("date") != twse_governed_source_date:
                raise ValueError("twse_governed_source_date_mismatch")
            trade_date = _source_date(root["date"], "Gregorian_YYYYMMDD")
        else:
            if not isinstance(root, list) or not all(isinstance(row, dict) for row in root):
                raise ValueError("tpex_root_invalid")
            rows = root
            fields = sorted({key for row in rows for key in row})
            dates = {_source_date(row["Date"], "ROC_YYYMMDD") for row in rows}
            if len(dates) != 1:
                raise ValueError("tpex_multiple_or_missing_source_dates")
            trade_date = next(iter(dates))
        if not rows or source["code_field"] not in fields:
            raise ValueError("required_security_code_missing")
        required = set()
        for group in CORE_GROUPS:
            for expression in source["required_common_core"][group].values():
                required.update(expression)
        required.update(source["required_common_core"]["institutional_total_net_shares"])
        required.add(source["code_field"])
        if market == "TWSE":
            required.add(source["source_native_optional"]["security_name"])
        if not required.issubset(fields):
            raise ValueError("required_source_fields_missing")
        index: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            code = row[source["code_field"]]
            if not isinstance(code, str) or not code:
                raise ValueError("security_code_invalid")
            normalized = _normalized_row(row, source, market)
            index.setdefault(code, []).append(normalized)
        return PreparedSource(market, trade_date, index, len(rows), len(fields), None)
    except (UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError, OverflowError) as error:
        code = str(error) if isinstance(error, ValueError) else type(error).__name__
        return PreparedSource(market, None, {}, 0, 0, code[:80])


def validate_evidence(evidence: dict[str, Any]) -> None:
    schema = json.loads((ROOT / "schemas/cash_institutional_flow_context_evidence.v1.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(evidence))
    if errors:
        raise ValueError("i3_evidence_schema_invalid:" + errors[0].message)
