"""Dormant, zero-network H2 corporate-action source normalizers.

These functions accept only caller-supplied official-source-shaped rows.  They
are deliberately not runtime adapters and do not acquire, persist, or register
any source.  PRE and FINAL sources remain independently observable evidence.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from pathlib import Path
import json

from jsonschema import Draft7Validator

from scripts.validate_phase_h_v3_contracts import validate_corporate_action_context_semantics


DECLARED_EVENT_SUBTYPES = (
    "ex_dividend", "ex_right", "ex_right_dividend", "capital_reduction_resume",
    "par_value_change_resume", "split", "reverse_split", "share_consolidation",
    "cash_capital_increase_effect", "other_official_reference_price_event",
)
_NUMERIC_STATES = {"value", "blank", "not_announced", "not_applicable", "unavailable", "source_failed"}
_MISSING = object()


class H2NormalizationError(ValueError):
    """A deterministic source-contract or exact-binding failure."""


def _descriptor(source_id: str) -> dict:
    descriptors = json.loads((Path(__file__).resolve().parents[2] / "config" / "phase_h_h2_dormant_source_descriptors.json").read_text(encoding="utf-8"))
    return deepcopy(next(item for item in descriptors["sources"] if item["source_id"] == source_id))


def _source(source_id: str) -> dict:
    value = _descriptor(source_id)
    return {key: value[key] for key in ("source_family", "source_contract_id", "transport", "license_authority", "source_role", "activation_state")}


def failed_source_result(source_id: str, diagnostic: str, *, binding_failed: bool = False) -> dict:
    """Turn a caught source-contract/binding failure into deterministic input for assembly.

    The normalizers fail closed before an event is created.  A caller that is
    assembling several source results may retain that failure without turning it
    into a healthy no-row result.
    """
    return {"source": _source(source_id), "status": "binding_failed" if binding_failed else "source_failed", "events": [], "covered": (), "caveats": [diagnostic]}


def _typed(raw: object = _MISSING, *, absent: str = "unavailable") -> dict:
    if raw is _MISSING or raw is None:
        return {"state": absent, "value": None}
    if isinstance(raw, str):
        text = raw.strip()
        if text == "":
            return {"state": "blank", "value": None}
        if text == "尚未公告":
            return {"state": "not_announced", "value": None}
        try:
            raw = float(text)
        except ValueError as exc:
            raise H2NormalizationError("invalid_numeric_field") from exc
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise H2NormalizationError("invalid_numeric_field")
    return {"state": "value", "value": raw}


def _event_type(cash: dict, stock: dict, rights: dict) -> str:
    """Classify only when every classification input is an explicit number."""
    if any(item.get("state") != "value" for item in (cash, stock, rights)):
        raise H2NormalizationError("source_failed:event_type_unresolved")
    cash_value, stock_value, rights_value = (item["value"] for item in (cash, stock, rights))
    if cash_value > 0 and (stock_value > 0 or rights_value > 0):
        return "ex_right_dividend"
    if cash_value > 0:
        return "ex_dividend"
    if stock_value > 0 or rights_value > 0:
        return "ex_right"
    raise H2NormalizationError("source_failed:event_type_unresolved")


def _binding_row(rows: object, target: Mapping[str, str], *, market: str, identifier: str, required: Sequence[str]) -> Mapping[str, object] | None:
    if target.get("market") != market:
        raise H2NormalizationError("binding_failed:wrong_market")
    if not isinstance(rows, list) or any(not isinstance(row, Mapping) for row in rows):
        raise H2NormalizationError("source_failed:invalid_top_level_rows")
    for row in rows:
        missing = [field for field in required if field not in row]
        if missing:
            raise H2NormalizationError(f"source_failed:missing_required_field:{missing[0]}")
    matches = [row for row in rows if str(row[identifier]) == target.get("security_code")]
    if not matches:
        return None
    if len(matches) != 1:
        raise H2NormalizationError("binding_failed:ambiguous_exact_target_rows")
    return matches[0]


def _event(*, stage: str, lifecycle: str, event_type: str, effective_date: object, announcement_date: object, pre_close: dict, reference: dict, cash: dict, stock: dict, rights: dict, subscription: dict, citation_id: str, source_proof: str | None = None) -> dict:
    if not isinstance(effective_date, str) or not effective_date:
        raise H2NormalizationError("source_failed:missing_event_date")
    return {
        "event_type": event_type, "source_evidence_stage": stage, "event_lifecycle": lifecycle,
        "announcement_date": announcement_date if isinstance(announcement_date, str) else None,
        "effective_date": effective_date, "pre_event_close": pre_close,
        "official_reference_price": reference, "opening_reference_basis": None,
        "cash_dividend": cash, "stock_dividend_ratio": stock, "rights_ratio": rights,
        "subscription_price": subscription, "official_source_proof": source_proof,
        "revision_relation": {"status": "unresolved", "relation_type": None, "related_official_reference": None},
        "citation_ids": [citation_id],
    }


def normalize_tpex_exright_prepost(rows: object, target: Mapping[str, str], *, observed_at: str, citation_id: str) -> dict:
    required = ("SecuritiesCompanyCode", "ExRrightsExDividendDate", "ExRrightsExDividend", "CashDividend", "StockDividendRatio", "SubscriptionRatioToNewSharesIssued", "SubscriptionPricePerShare")
    row = _binding_row(rows, target, market="TPEX", identifier="SecuritiesCompanyCode", required=required)
    source = _source("H2-TPEX-EXRIGHT-PRE-OPENAPI")
    if row is None:
        return {"source": source, "status": "no_evidence_in_covered_scope", "events": [], "covered": ("ex_dividend", "ex_right", "ex_right_dividend"), "caveats": []}
    cash, stock, rights, subscription = (_typed(row[key]) for key in ("CashDividend", "StockDividendRatio", "SubscriptionRatioToNewSharesIssued", "SubscriptionPricePerShare"))
    return {"source": source, "status": "available", "covered": ("ex_dividend", "ex_right", "ex_right_dividend"), "caveats": [], "events": [_event(stage="preannouncement", lifecycle="scheduled", event_type=_event_type(cash, stock, rights), effective_date=row["ExRrightsExDividendDate"], announcement_date=None, pre_close={"state": "not_announced", "value": None}, reference={"state": "not_announced", "value": None}, cash=cash, stock=stock, rights=rights, subscription=subscription, citation_id=citation_id, source_proof="tpex_exright_prepost")]}


def normalize_tpex_exright_daily(rows: object, target: Mapping[str, str], *, observed_at: str, citation_id: str) -> dict:
    required = ("SecuritiesCompanyCode", "Date", "ClosePriceBeforeExRightsDiviend", "ExRightsDiviendQuote", "StockDividend", "CashDividend", "ExRightsDiviend", "OpeningReferencePrice", "SubscriptionPricePerShare")
    row = _binding_row(rows, target, market="TPEX", identifier="SecuritiesCompanyCode", required=required)
    source = _source("H2-TPEX-EXRIGHT-FINAL-OPENAPI")
    if row is None:
        return {"source": source, "status": "no_evidence_in_covered_scope", "events": [], "covered": ("ex_dividend", "ex_right", "ex_right_dividend"), "caveats": []}
    pre_close, reference, cash, stock, rights, subscription = (_typed(row[key], absent="unavailable") for key in ("ClosePriceBeforeExRightsDiviend", "ExRightsDiviendQuote", "CashDividend", "StockDividend", "ExRightsDiviend", "SubscriptionPricePerShare"))
    return {"source": source, "status": "available", "covered": ("ex_dividend", "ex_right", "ex_right_dividend"), "caveats": [], "events": [_event(stage="official_reference_calculated", lifecycle="effective", event_type=_event_type(cash, stock, rights), effective_date=row["Date"], announcement_date=row.get("Date"), pre_close=pre_close, reference=reference, cash=cash, stock=stock, rights=rights, subscription=subscription, citation_id=citation_id, source_proof="tpex_exright_daily")]}


def normalize_twse_twt48u_all(rows: object, target: Mapping[str, str], *, observed_at: str, citation_id: str) -> dict:
    required = ("Code", "Date", "Exdividend", "StockDividendRatio", "SubscriptionRatio", "SubscriptionPricePerShare", "CashDividend")
    row = _binding_row(rows, target, market="TWSE", identifier="Code", required=required)
    source = _source("H2-TWSE-EXRIGHT-PRE-OPENAPI")
    if row is None:
        return {"source": source, "status": "no_evidence_in_covered_scope", "events": [], "covered": ("ex_dividend", "ex_right", "ex_right_dividend"), "caveats": []}
    cash, stock, rights, subscription = (_typed(row[key]) for key in ("CashDividend", "StockDividendRatio", "SubscriptionRatio", "SubscriptionPricePerShare"))
    return {"source": source, "status": "available", "covered": ("ex_dividend", "ex_right", "ex_right_dividend"), "caveats": [], "events": [_event(stage="preannouncement", lifecycle="scheduled", event_type=_event_type(cash, stock, rights), effective_date=row["Date"], announcement_date=None, pre_close={"state": "not_announced", "value": None}, reference={"state": "not_announced", "value": None}, cash=cash, stock=stock, rights=rights, subscription=subscription, citation_id=citation_id, source_proof="TWT48U_ALL")]}


def assemble_corporate_action_context(results: Sequence[Mapping[str, object]], target: Mapping[str, str], *, observed_at: str, requested_window: Mapping[str, str]) -> dict:
    """Assemble source results without claiming uncovered H2 scope is absent."""
    if not results:
        raise H2NormalizationError("source_failed:no_source_results")
    sources = sorted((deepcopy(item["source"]) for item in results), key=lambda x: (x["source_family"], x["source_contract_id"]))
    events = sorted((deepcopy(event) for item in results for event in item["events"]), key=lambda x: (x["effective_date"] or "", x["source_evidence_stage"], x["citation_ids"][0]))
    covered = sorted({subtype for item in results for subtype in item["covered"]})
    uncovered = sorted(set(DECLARED_EVENT_SUBTYPES) - set(covered))
    statuses = {item["status"] for item in results}
    source_failed = any(str(status).startswith("source_failed") for status in statuses)
    binding_failed = any(str(status).startswith("binding_failed") for status in statuses)
    failed_sources = sorted({item["source"]["source_family"] for item in results if str(item["status"]).startswith("source_failed")})
    if source_failed:
        status, coverage_status = "source_failed", "source_failed"
    elif binding_failed:
        status, coverage_status = "binding_failed", "binding_failed"
    else:
        status, coverage_status = ("partial", "partial")
    value = {"schema_version": "corporate_action_context_evidence.v1", "status": status, "target": dict(target), "coverage": {"status": coverage_status, "declared_scope_complete": False, "retrieval_succeeded": not source_failed, "source_contract_validated": not source_failed, "exact_target_search_succeeded": not binding_failed, "requested_window": dict(requested_window), "declared_event_subtypes": list(DECLARED_EVENT_SUBTYPES), "covered_event_subtypes": covered, "uncovered_event_subtypes": uncovered, "failed_source_families": failed_sources}, "sources": sources, "observed_at": observed_at, "events": events, "caveats": sorted({caveat for item in results for caveat in item.get("caveats", [])}), "citation_ids": sorted({citation for event in events for citation in event["citation_ids"]})}
    root = Path(__file__).resolve().parents[2]
    schema = json.loads((root / "schemas" / "corporate_action_context_evidence.v1.schema.json").read_text(encoding="utf-8"))
    errors = list(Draft7Validator(schema).iter_errors(value))
    if errors:
        raise H2NormalizationError(f"assembled_h2_schema_invalid:{errors[0].message}")
    try:
        validate_corporate_action_context_semantics(value)
    except ValueError as exc:
        raise H2NormalizationError(f"assembled_h2_semantics_invalid:{exc}") from exc
    return value
