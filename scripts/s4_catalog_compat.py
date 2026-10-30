"""Pure, exact S4 descriptive compatibility authority; never runtime discovery.

Only the canonical Catalog's three Owner-authorized leaves are projected.
Callers retain their pinned baseline and strict final equality comparison.
"""
from __future__ import annotations

import copy

CATALOG = "docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json"

# Owner-authorized post-v1.5 S4 descriptive reconciliation only (2026-10-30).
# Exact predecessor -> successor values, not ignored fields or a baseline reset.
# See POST_V1_5_CURRENT_AUTHORITY_STABILIZATION_S4_CATALOG_MCP_CURRENT_TRUTH_RECONCILIATION_2026-10-30.md.
S4_TOP_LIMITATION_DELTAS = (
    (4, 'H1 trading-status coverage remains partial; H1-TPEX-ATTENTION-OPENAPI is the only active H1 route',
     'H1 trading-status coverage remains partial; the selected TPEx composite provides canonical attention and disposition plus source-native cmode with unresolved semantics and zero canonical coverage; changed_trading_method, suspension, and resumption remain uncovered; no TWSE H1 route is active'),
    (5, 'H2 remains inactive; H3 runtime execution is limited to the Owner-accepted H3-TWSE-DEFAULT-BOUNDED route; TPEX H3 remains blocked and non-executable',
     'H2 execution is limited to TWSE TWT48U_ALL preannouncement using the successful same-target H3-derived comparison window; no full historical coverage or final TWT49U evidence is provided, TPEx routes remain inactive, and subtype coverage remains incomplete; H3 runtime execution is limited to the Owner-accepted H3-TWSE-DEFAULT-BOUNDED route; TPEX H3 remains blocked and non-executable'),
)
S4_SESSION_DESCRIPTION_DELTA = (
    'Retrieves the market session status, local clock and closure states.',
    'Models market session status, local clock and closure states; the current Unified route is blocked with no selected executor and is not currently executable.',
)


def _validated_session(document: dict, *, successor: bool) -> dict:
    """Require one target row and unique exact leaves in their fixed positions."""
    side = "successor" if successor else "predecessor"
    def reject(detail):
        raise ValueError(f"S4 {side} mismatch: {detail}")
    if not isinstance(document, dict):
        reject("Catalog object")
    rows = document.get("data_need_capabilities")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        reject("capability rows")
    matches = [row for row in rows if row.get("capability_id") == "session_status"]
    if len(matches) != 1:
        reject("session_status cardinality")
    session = matches[0]
    if session.get("description") != S4_SESSION_DESCRIPTION_DELTA[int(successor)]:
        reject("session_status description")
    limitations = document.get("known_limitations")
    if not isinstance(limitations, list):
        reject("top-level limitations")
    for index, before, after in S4_TOP_LIMITATION_DELTAS:
        expected, opposite = (after, before) if successor else (before, after)
        if (len(limitations) <= index or limitations[index] != expected
                or limitations.count(expected) != 1 or opposite in limitations):
            reject(f"known_limitations/{index}")
    return session


def s4_expected_catalog(baseline: dict) -> dict:
    """Construct the exact current successor view without changing historical input."""
    _validated_session(baseline, successor=False)
    expected = copy.deepcopy(baseline)
    for index, _, after in S4_TOP_LIMITATION_DELTAS:
        expected["known_limitations"][index] = after
    next(row for row in expected["data_need_capabilities"]
         if row["capability_id"] == "session_status")["description"] = S4_SESSION_DESCRIPTION_DELTA[1]
    return expected


def project_s4_catalog(relative: str, current, historical):
    """Validate exact S4 successors/predecessors, then restore only three leaves.

    Other documents are returned unchanged. Unrelated Catalog drift is retained
    for the caller's strict historical comparison, never discarded or blessed.
    """
    if relative != CATALOG:
        return current
    _validated_session(current, successor=True)
    _validated_session(historical, successor=False)
    projected = copy.deepcopy(current)
    for index, before, _ in S4_TOP_LIMITATION_DELTAS:
        projected["known_limitations"][index] = before
    next(row for row in projected["data_need_capabilities"]
         if row["capability_id"] == "session_status")["description"] = S4_SESSION_DESCRIPTION_DELTA[0]
    return projected
