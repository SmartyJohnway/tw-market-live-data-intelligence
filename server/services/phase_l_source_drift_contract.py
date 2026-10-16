"""Pure, private observations for deterministic Phase L source-drift contracts.

This module does not acquire sources or schedule work. Callers must supply
already-observed facts and source-specific semantic outcomes; this layer only
preserves bounded observations and never decides that a source was removed or
that a target universe is invalid.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime, format_datetime
import re
from typing import Literal


# Representation bound only. This is not a retry duration or dispatch policy.
MAX_RETRY_AFTER_DELTA_SECONDS = 2_147_483_647
_DELTA_SECONDS = re.compile(r"^[0-9]+$")
_SEMANTIC_OUTCOMES = {
    "unknown",
    "available",
    "partial",
    "missing",
    "unavailable",
    "no_evidence_in_covered_scope",
    "not_yet_available",
    "currentness_unknown",
    "stale",
    "source_failed",
    "binding_failed",
}
_CONTRACT_OUTCOMES = {"unknown", "valid", "invalid", "not_evaluated"}
_EMPTY_FORMS = {"unknown", "empty_body", "empty_collection", "nonempty"}
_EMPTY_POLICIES = {"unknown", "allowed", "invalid"}
_TARGET_BINDINGS = {"unknown", "matched", "absent", "ambiguous"}


@dataclass(frozen=True, slots=True)
class RetryAfterFact:
    present: bool
    kind: Literal["absent", "delta_seconds", "http_date", "invalid", "out_of_range"]
    delta_seconds: int | None = None
    http_date: str | None = None


@dataclass(frozen=True, slots=True)
class SourceDriftObservation:
    source_contract_id: str
    observed_at: str
    http_status: int | None
    transport_outcome: str
    contract_outcome: str
    semantic_outcome: str
    retry_after: RetryAfterFact
    drift_observations: tuple[str, ...]
    response_form: str
    empty_response_policy: str
    previous_row_count: int | None
    current_row_count: int | None
    observed_row_delta: int | None
    target_binding: str
    source_reported_period: str | None
    requested_period: str | None
    adjudication: str

    def as_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["retry_after"] = asdict(self.retry_after)
        value["drift_observations"] = list(self.drift_observations)
        return value


def _normalize_http_date(value: str) -> str | None:
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        return None
    return format_datetime(parsed.astimezone(timezone.utc), usegmt=True)


def _has_explicit_timezone(value: str) -> bool:
    """Accept ISO-8601 timestamps only when they identify an offset."""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError, OverflowError):
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def parse_retry_after(value: str | None) -> RetryAfterFact:
    """Parse Retry-After as a fact only; never sleep or schedule a retry."""
    if value is None:
        return RetryAfterFact(present=False, kind="absent")
    if not isinstance(value, str):
        return RetryAfterFact(present=True, kind="invalid")
    raw = value.strip()
    if _DELTA_SECONDS.fullmatch(raw):
        seconds = int(raw)
        if seconds > MAX_RETRY_AFTER_DELTA_SECONDS:
            return RetryAfterFact(present=True, kind="out_of_range")
        return RetryAfterFact(present=True, kind="delta_seconds", delta_seconds=seconds)
    normalized_date = _normalize_http_date(raw)
    if normalized_date is not None:
        return RetryAfterFact(present=True, kind="http_date", http_date=normalized_date)
    return RetryAfterFact(present=True, kind="invalid")


def observe_source_attempt(
    *,
    source_contract_id: str,
    observed_at: str,
    http_status: int | None,
    retry_after: str | None = None,
    transport_outcome: str = "http_response",
    contract_outcome: str = "unknown",
    semantic_outcome: str = "unknown",
    response_form: str = "unknown",
    empty_response_policy: str = "unknown",
    previous_row_count: int | None = None,
    current_row_count: int | None = None,
    target_binding: str = "unknown",
    source_reported_period: str | None = None,
    requested_period: str | None = None,
) -> SourceDriftObservation:
    """Project supplied facts without provider-health or retry conclusions.

    `empty_response_policy` and semantic/contract outcomes must come from the
    exact source contract. No body text is accepted or inspected here.
    """
    if not isinstance(source_contract_id, str) or not source_contract_id.strip():
        raise ValueError("source_contract_id_required")
    if not isinstance(observed_at, str) or not _has_explicit_timezone(observed_at):
        raise ValueError("observed_at_invalid")
    if http_status is not None and (type(http_status) is not int or not 100 <= http_status <= 599):
        raise ValueError("http_status_invalid")
    if transport_outcome not in {"http_response", "transport_failure", "unknown"}:
        raise ValueError("transport_outcome_invalid")
    if transport_outcome == "transport_failure" and http_status is not None:
        raise ValueError("transport_http_status_conflict")
    if transport_outcome == "http_response" and http_status is None:
        raise ValueError("http_response_status_required")
    if contract_outcome not in _CONTRACT_OUTCOMES:
        raise ValueError("contract_outcome_invalid")
    if semantic_outcome not in _SEMANTIC_OUTCOMES:
        raise ValueError("semantic_outcome_invalid")
    if response_form not in _EMPTY_FORMS or empty_response_policy not in _EMPTY_POLICIES:
        raise ValueError("empty_response_contract_invalid")
    if response_form in {"empty_body", "empty_collection"} and semantic_outcome == "available":
        raise ValueError("empty_response_available_conflict")
    if target_binding not in _TARGET_BINDINGS:
        raise ValueError("target_binding_invalid")
    for name, period in (("source_reported_period", source_reported_period), ("requested_period", requested_period)):
        if period is not None and (not isinstance(period, str) or len(period) > 64):
            raise ValueError(f"{name}_invalid")
    for name, count in (("previous_row_count", previous_row_count), ("current_row_count", current_row_count)):
        if count is not None and (type(count) is not int or count < 0):
            raise ValueError(f"{name}_invalid")

    if semantic_outcome in {"not_yet_available", "currentness_unknown"}:
        response_is_adjudicable = (
            transport_outcome == "http_response"
            and http_status is not None
            and 200 <= http_status < 300
            and contract_outcome == "valid"
        )
        if not response_is_adjudicable:
            raise ValueError("semantic_outcome_requires_valid_response")

    facts: list[str] = []
    if http_status == 429:
        facts.append("rate_limit_observed")
    elif http_status == 404:
        facts.append("endpoint_not_found_observed")
    elif http_status == 410:
        facts.append("endpoint_gone_observed")

    retry_fact = parse_retry_after(retry_after)
    if retry_fact.kind in {"invalid", "out_of_range"}:
        facts.append("retry_after_unparseable")
    if semantic_outcome == "not_yet_available":
        facts.append("publication_delay_observed")
    if semantic_outcome == "currentness_unknown":
        facts.append("currentness_unknown")
    if target_binding in {"absent", "ambiguous"}:
        facts.append("target_scope_change_observed")

    delta = None
    if previous_row_count is not None and current_row_count is not None:
        delta = current_row_count - previous_row_count
        if delta:
            facts.append("observed_universe_delta")

    if response_form in {"empty_body", "empty_collection"}:
        facts.append("empty_response_observed")

    if transport_outcome == "transport_failure" or (http_status is not None and not 200 <= http_status < 300):
        adjudication = "TRANSPORT_FAILURE_REPORTED" if transport_outcome == "transport_failure" else "HTTP_FAILURE_REPORTED"
    elif contract_outcome == "invalid":
        adjudication = "CONTRACT_FAILURE_REPORTED"
    elif response_form in {"empty_body", "empty_collection"} and empty_response_policy == "invalid":
        adjudication = "SOURCE_CONTRACT_REJECTS_EMPTY_RESPONSE"
    elif target_binding == "ambiguous":
        adjudication = "SOURCE_SPECIFIC_TARGET_ADJUDICATION_REQUIRED"
    else:
        # In particular, a row-count delta or a previous-period value alone
        # never determines whether evidence is valid, stale, or current.
        adjudication = "SOURCE_SPECIFIC_SEMANTICS_PRESERVED"

    return SourceDriftObservation(
        source_contract_id=source_contract_id.strip(), observed_at=observed_at,
        http_status=http_status, transport_outcome=transport_outcome,
        contract_outcome=contract_outcome, semantic_outcome=semantic_outcome,
        retry_after=retry_fact, drift_observations=tuple(sorted(set(facts))),
        response_form=response_form, empty_response_policy=empty_response_policy,
        previous_row_count=previous_row_count, current_row_count=current_row_count,
        observed_row_delta=delta, target_binding=target_binding, adjudication=adjudication,
        source_reported_period=source_reported_period, requested_period=requested_period,
    )
