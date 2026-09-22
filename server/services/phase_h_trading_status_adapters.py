"""Dormant, zero-network H1 trading-status source normalizers.

The functions accept caller-supplied official-source-shaped rows only.  They
do not acquire, persist, register, or activate any Phase H source.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
import json
from pathlib import Path
import re

from jsonschema import Draft7Validator

from scripts.validate_phase_h_v3_contracts import validate_trading_status_context_semantics


DECLARED_STATUS_TYPES = (
    "attention", "disposition", "changed_trading_method", "suspension", "resumption",
)


class H1NormalizationError(ValueError):
    """A deterministic source-contract or exact-binding failure."""


def _descriptor(source_id: str) -> dict:
    root = Path(__file__).resolve().parents[2]
    descriptors = json.loads((root / "config" / "phase_h_h1_dormant_source_descriptors.json").read_text(encoding="utf-8"))
    return deepcopy(next(item for item in descriptors["sources"] if item["source_id"] == source_id))


def _source(source_id: str) -> dict:
    value = _descriptor(source_id)
    return {key: value[key] for key in ("source_family", "source_contract_id", "transport", "license_authority", "source_role", "activation_state")}


def _validated_rows(rows: object, target: Mapping[str, str], *, market: str, required: Sequence[str]) -> list[Mapping[str, object]]:
    if target.get("market") != market:
        raise H1NormalizationError("binding_failed:wrong_market")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise H1NormalizationError("source_failed:invalid_top_level_rows")
    for row in rows:
        missing = [field for field in required if field not in row]
        if missing:
            raise H1NormalizationError(f"source_failed:missing_required_field:{missing[0]}")
    return rows


def _date_value(raw: object) -> str | None:
    """Normalize only an already canonical date; do not assume source grammar."""
    if isinstance(raw, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return raw
    return None


def _snapshot_date(rows: Sequence[Mapping[str, object]], field: str) -> tuple[str | None, list[str]]:
    if not rows:
        return None, []
    raw_values = {row[field] for row in rows}
    if len(raw_values) != 1:
        return None, [f"source_snapshot_date_unresolved:{field}:multiple_values"]
    normalized = _date_value(next(iter(raw_values)))
    if normalized is None:
        return None, [f"source_snapshot_date_unresolved:{field}:raw_encoding"]
    return normalized, []


def _bound_row(rows: Sequence[Mapping[str, object]], *, identifier: str, target: Mapping[str, str]) -> Mapping[str, object] | None:
    matches = [row for row in rows if str(row[identifier]) == target.get("security_code")]
    if not matches:
        return None
    if len(matches) != 1:
        raise H1NormalizationError("binding_failed:ambiguous_exact_target_rows")
    return matches[0]


def _item(*, status_type: str, source_record_date: str | None, reason: object, conditions: object, measures: object, provenance: Mapping[str, object], citation_id: str) -> dict:
    def text(value: object) -> str | None:
        return value if isinstance(value, str) else None

    return {
        "status_type": status_type,
        "status_lifecycle": "reported",
        "published_at": None,
        "source_record_date": source_record_date,
        "effective_from": None,
        "effective_to": None,
        "official_reason": text(reason),
        "official_conditions": text(conditions),
        "official_measures": text(measures),
        "source_native_provenance": dict(provenance),
        "citation_ids": [citation_id],
    }


def _result(*, source_id: str, target: Mapping[str, str], observed_at: str, snapshot_date: str | None, covered: Sequence[str], items: Sequence[Mapping[str, object]], citation_ids: Sequence[str], status: str = "partial", caveats: Sequence[str] = (), failed_source: bool = False, binding_failed: bool = False) -> dict:
    covered_set = set(covered)
    value = {
        "schema_version": "trading_status_context_evidence.v1",
        "status": status,
        "target": dict(target),
        "coverage": {
            "status": "source_failed" if failed_source else "binding_failed" if binding_failed else "partial",
            "declared_scope_complete": False,
            "retrieval_succeeded": not failed_source,
            "source_contract_validated": not failed_source,
            "exact_target_search_succeeded": not binding_failed,
            "source_snapshot_date": snapshot_date,
            "declared_status_types": list(DECLARED_STATUS_TYPES),
            "covered_status_types": sorted(covered_set),
            "uncovered_status_types": sorted(set(DECLARED_STATUS_TYPES) - covered_set),
            "failed_source_families": [_source(source_id)["source_family"]] if failed_source else [],
        },
        "source": _source(source_id),
        "observed_at": observed_at,
        "items": [deepcopy(item) for item in items],
        "caveats": sorted(set(caveats)),
        "citation_ids": sorted({citation for citation in citation_ids if isinstance(citation, str) and citation}),
    }
    root = Path(__file__).resolve().parents[2]
    schema = json.loads((root / "schemas" / "trading_status_context_evidence.v1.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft7Validator(schema).iter_errors(value))
    if errors:
        raise H1NormalizationError(f"assembled_h1_schema_invalid:{errors[0].message}")
    try:
        validate_trading_status_context_semantics(value)
    except ValueError as exc:
        raise H1NormalizationError(f"assembled_h1_semantics_invalid:{exc}") from exc
    return value


def failed_source_result(source_id: str, target: Mapping[str, str], *, observed_at: str, diagnostic: str, citation_id: str | None = None, binding_failed: bool = False) -> dict:
    """Preserve caller-supplied source provenance for a non-event failure."""
    return _result(source_id=source_id, target=target, observed_at=observed_at, snapshot_date=None, covered=(), items=(), citation_ids=[citation_id] if citation_id else [], status="binding_failed" if binding_failed else "source_failed", caveats=[diagnostic], failed_source=not binding_failed, binding_failed=binding_failed)


def normalize_tpex_attention(rows: object, target: Mapping[str, str], *, observed_at: str, citation_id: str) -> dict:
    required = ("Date", "SecuritiesCompanyCode", "CompanyName", "TradingInformation", "ClosePrice", "PriceEarningRatio")
    valid_rows = _validated_rows(rows, target, market="TPEX", required=required)
    snapshot_date, date_caveats = _snapshot_date(valid_rows, "Date")
    row = _bound_row(valid_rows, identifier="SecuritiesCompanyCode", target=target)
    items = [] if row is None else [_item(status_type="attention", source_record_date=_date_value(row["Date"]), reason=row["TradingInformation"], conditions=None, measures=None, provenance={key: row[key] for key in required}, citation_id=citation_id)]
    return _result(source_id="H1-TPEX-ATTENTION-OPENAPI", target=target, observed_at=observed_at, snapshot_date=snapshot_date, covered=("attention",), items=items, citation_ids=[citation_id], caveats=date_caveats)


def normalize_tpex_disposition(rows: object, target: Mapping[str, str], *, observed_at: str, citation_id: str) -> dict:
    required = ("Date", "SecuritiesCompanyCode", "CompanyName", "DispositionPeriod", "DispositionReasons", "DisposalCondition")
    valid_rows = _validated_rows(rows, target, market="TPEX", required=required)
    snapshot_date, date_caveats = _snapshot_date(valid_rows, "Date")
    row = _bound_row(valid_rows, identifier="SecuritiesCompanyCode", target=target)
    items = [] if row is None else [_item(status_type="disposition", source_record_date=_date_value(row["Date"]), reason=row["DispositionReasons"], conditions=row["DisposalCondition"], measures=None, provenance={key: row[key] for key in required}, citation_id=citation_id)]
    return _result(source_id="H1-TPEX-DISPOSITION-OPENAPI", target=target, observed_at=observed_at, snapshot_date=snapshot_date, covered=("disposition",), items=items, citation_ids=[citation_id], caveats=date_caveats)


def normalize_twse_changed_trading(rows: object, target: Mapping[str, str], *, observed_at: str, citation_id: str) -> dict:
    required = ("Code", "Name", "PeriodicCallAuctionTrading")
    valid_rows = _validated_rows(rows, target, market="TWSE", required=required)
    row = _bound_row(valid_rows, identifier="Code", target=target)
    items = [] if row is None else [_item(status_type="changed_trading_method", source_record_date=None, reason=None, conditions=None, measures=None, provenance={key: row[key] for key in required}, citation_id=citation_id)]
    return _result(source_id="H1-TWSE-CHANGED-TRADING-OPENAPI", target=target, observed_at=observed_at, snapshot_date=None, covered=("changed_trading_method",), items=items, citation_ids=[citation_id])
