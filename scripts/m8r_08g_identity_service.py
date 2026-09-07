"""Installation-local Taiwan Market Identity Service.

This module deliberately separates durable instrument identity from the
listing/routing identity consumed by the existing Unified Market Evidence v1
contracts.  It has no network, scheduler, or persistence side effects.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from typing import Any


CASH_MARKETS = frozenset({"TWSE", "TPEX"})
EXECUTABLE_INSTRUMENT_TYPES = frozenset({"common_share", "etf"})
OFFICIAL_SUCCESSOR_EVENT_TYPES = frozenset({"official_isin_successor", "isin_successor"})


def normalize_name(value: str | None) -> str:
    return re.sub(r"\s+", "", value or "").casefold()


def listing_id(record: dict[str, Any]) -> str:
    value = record.get("listing_id") or record.get("canonical_target_id")
    if not isinstance(value, str) or ":" not in value:
        raise ValueError("invalid_listing_routing_identity")
    return value


def instrument_id(record: dict[str, Any]) -> str | None:
    """Return the durable cash-instrument identity without inventing one."""
    identity = record.get("identity") or {}
    market = (record.get("classification") or {}).get("market")
    isin = identity.get("isin")
    if market in CASH_MARKETS:
        return isin.upper() if isinstance(isin, str) and isin else None
    explicit = record.get("instrument_id")
    return explicit if isinstance(explicit, str) and explicit else None


def projected_execution_eligibility(record: dict[str, Any]) -> dict[str, Any]:
    """Keep the knowledge universe broad while constraining execution routes."""
    existing = copy.deepcopy(record.get("execution_eligibility") or {})
    classification = record.get("classification") or {}
    instrument_type = classification.get("instrument_type")
    normalized_type = instrument_type.casefold() if isinstance(instrument_type, str) else None
    market = classification.get("market")
    if market in CASH_MARKETS and normalized_type not in EXECUTABLE_INSTRUMENT_TYPES:
        reasons = set(existing.get("reason_codes") or [])
        reasons.add("unsupported_instrument_type")
        return {"status": "blocked", "reason_codes": sorted(reasons)}
    reasons = set(existing.get("reason_codes") or [])
    # The legacy compact index predates ETF execution eligibility and may have
    # classified every ETF with this generic reason.  Preserve independent
    # lifecycle blocks, but do not carry that obsolete type-only block forward.
    reasons.discard("unsupported_instrument_type")
    if not reasons:
        return {"status": "allowed", "reason_codes": []}
    return {
        "status": existing.get("status", "blocked"),
        "reason_codes": sorted(reasons),
    }


def official_successor_migration(record: dict[str, Any]) -> dict[str, Any] | None:
    """Project an official ISIN successor as review-required, never a rewrite.

    The current instrument remains the record's durable identity.  A future
    persistent consumer must obtain user review before it applies a successor.
    """
    current_isin = instrument_id(record)
    lifecycle = record.get("lifecycle") or {}
    for event in lifecycle.get("events") or []:
        if not isinstance(event, dict):
            continue
        event_type = event.get("event_type") or event.get("type")
        predecessor = event.get("predecessor_isin") or event.get("old_isin")
        successor = event.get("successor_isin") or event.get("new_isin")
        official = event.get("official_evidence") is True or event_type in OFFICIAL_SUCCESSOR_EVENT_TYPES
        if official and predecessor == current_isin and isinstance(successor, str) and successor and successor != predecessor:
            return {
                "status": "IDENTITY_MIGRATION_REVIEW_REQUIRED",
                "predecessor": predecessor,
                "successor": successor,
                "reason": event.get("reason") or event_type,
                "event_id": event.get("event_id"),
                "evidence": copy.deepcopy(event.get("evidence") or event.get("evidence_refs") or []),
                "review_required": True,
            }
    return None


def project_release_record(record: dict[str, Any]) -> dict[str, Any]:
    """Create an additive v1-compatible record projection for a local release."""
    projected = copy.deepcopy(record)
    projected["listing_id"] = listing_id(projected)
    projected["canonical_target_id"] = projected["listing_id"]
    projected["instrument_id"] = instrument_id(projected)
    projected["execution_eligibility"] = projected_execution_eligibility(projected)
    lifecycle = projected.get("lifecycle") or {}
    migration = official_successor_migration(projected)
    if migration is not None:
        projected["identity_migration"] = migration
    projected["listing_history"] = copy.deepcopy(projected.get("listing_history") or [])
    projected["current_listing"] = {
        "market": (projected.get("classification") or {}).get("market"),
        "security_code": (projected.get("identity") or {}).get("security_code"),
        "observed_as_of": lifecycle.get("as_of"),
        "evidence": "governed_snapshot_current_listing",
    }
    aliases = projected.get("aliases")
    if not isinstance(aliases, list):
        aliases = []
        for event in lifecycle.get("events") or []:
            for key in ("former_name", "alias", "previous_name"):
                value = event.get(key) if isinstance(event, dict) else None
                if isinstance(value, str) and value:
                    aliases.append({"value": value, "source": "official_lifecycle_event"})
        projected["aliases"] = aliases
    return projected


@dataclass(frozen=True)
class IdentityResolution:
    status: str
    selected: dict[str, Any] | None
    candidates: list[dict[str, Any]]
    reason_codes: list[str]


class TaiwanMarketIdentityService:
    """Read-only, release-bound identity knowledge and execution boundary."""

    def __init__(self, records: list[dict[str, Any]], *, release_id: str, manifest_hash: str):
        self.release_id = release_id
        self.manifest_hash = manifest_hash
        self.records = [project_release_record(record) for record in records]
        self._by_listing = {listing_id(record): record for record in self.records}
        self._by_isin: dict[str, list[dict[str, Any]]] = {}
        self._by_code: dict[tuple[str | None, str], list[dict[str, Any]]] = {}
        self._by_name: dict[str, list[dict[str, Any]]] = {}
        for record in self.records:
            identity = record.get("identity") or {}
            market = (record.get("classification") or {}).get("market")
            isin = instrument_id(record)
            if isin:
                self._by_isin.setdefault(isin, []).append(record)
            code = identity.get("security_code")
            if isinstance(code, str) and code:
                self._by_code.setdefault((market, code), []).append(record)
                self._by_code.setdefault((None, code), []).append(record)
            for value in (identity.get("security_name_zh"), identity.get("security_name_en")):
                normalized = normalize_name(value)
                if normalized:
                    self._by_name.setdefault(normalized, []).append(record)
            for alias in record.get("aliases") or []:
                value = alias.get("value") if isinstance(alias, dict) else alias
                normalized = normalize_name(value if isinstance(value, str) else None)
                if normalized:
                    self._by_name.setdefault(normalized, []).append(record)

    def describe(self, record: dict[str, Any]) -> dict[str, Any]:
        identity = record.get("identity") or {}
        classification = record.get("classification") or {}
        eligibility = record.get("execution_eligibility") or {}
        return {
            "instrument_id": instrument_id(record),
            "listing_id": listing_id(record),
            "canonical_target_id": listing_id(record),
            "market": classification.get("market"),
            "security_code": identity.get("security_code"),
            "isin": identity.get("isin"),
            "instrument_type": classification.get("instrument_type"),
            "execution_eligibility": copy.deepcopy(eligibility),
            "release_id": self.release_id,
            "release_manifest_hash": self.manifest_hash,
        }

    def get_lifecycle(self, listing_routing_id: str) -> dict[str, Any] | None:
        """Return only recorded lifecycle evidence for a known listing."""
        record = self._by_listing.get(listing_routing_id)
        if record is None:
            return None
        return {
            "lifecycle": copy.deepcopy(record.get("lifecycle") or {}),
            "identity_migration": copy.deepcopy(record.get("identity_migration")),
            "release_id": self.release_id,
            "release_manifest_hash": self.manifest_hash,
        }

    def resolve(self, query: str, *, market_hint: str | None = None) -> IdentityResolution:
        value = (query or "").strip()
        if not value:
            return IdentityResolution("not_found", None, [], ["empty_query"])
        candidates: list[dict[str, Any]]
        reason: str
        if value in self._by_listing:
            candidates, reason = [self._by_listing[value]], "exact_listing_id"
        elif re.fullmatch(r"[A-Z]{2}[A-Z0-9]{10}", value.upper()):
            candidates, reason = self._by_isin.get(value.upper(), []), "exact_isin"
        elif re.fullmatch(r"[A-Z0-9._-]{1,20}", value):
            candidates, reason = self._by_code.get((market_hint, value), []) if market_hint else self._by_code.get((None, value), []), "exact_scoped_code"
            if not candidates:
                candidates, reason = self._by_name.get(normalize_name(value), []), "exact_normalized_name"
        else:
            candidates, reason = self._by_name.get(normalize_name(value), []), "exact_normalized_name_or_official_alias"
        candidates = sorted(
            {listing_id(item): item for item in candidates}.values(),
            key=listing_id,
        )
        if not candidates:
            return IdentityResolution("not_found", None, [], [reason])
        if len(candidates) != 1:
            return IdentityResolution("ambiguous", None, candidates, [reason, "multiple_candidates"])
        return IdentityResolution("resolved", candidates[0], candidates, [reason])
