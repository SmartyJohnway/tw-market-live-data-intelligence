"""Fixed, reviewed historical authority chain for future I3-A0 attempts.

This module only constructs in-memory latch documents. It never reserves or
consumes an attempt and has no transport/network behavior.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_PATH = ROOT / "docs/governance/phase_i/PHASE_I_I3_A0_FUTURE_ATTEMPT_AUTHORITY_CHAIN_V1.json"
ANCHOR_FIELDS = {
    "attempt_1_record_sha256": "43ef038ffd33a455ae52eff18a8f08e52436164b6d27d6140090b368810df5e0",
    "p0_mapping_sha256": "e3af3d8b5ce11fe88f0c32efa45400126fe1991ec0c0725fbc3f480e2888638c",
    "p0_record_sha256": "8d58c1eb22941099f28e72e884c4686ddab1a66de752dfd343892e959fca118a",
    "p1_authority_sha256": "666108fdd187f3ec753acc2a258e3ea7bd9415cc371346b5f32dc231ea665240",
    "p1_record_sha256": "541b62d45d248d28e114d04628aac379dbd2f5b6d66d6ad07ae8cd4ee661a70c",
}
HASHED_PATHS = {
    "attempt_1_record_sha256": "docs/governance/phase_i/PHASE_I_I3_A0_CASH_INSTITUTIONAL_FLOW_SOURCE_TIMING_SYMMETRY_PREFLIGHT_2026-10-01.json",
    "p0_mapping_sha256": "docs/governance/phase_i/PHASE_I_I3_A0_CASH_INSTITUTIONAL_FLOW_PROBE_MAPPING_V1.json",
    "p0_record_sha256": "docs/governance/phase_i/PHASE_I_I3_A0_P0_OFFLINE_PROBE_HARNESS_CLOSURE_2026-10-01.json",
    "p1_authority_sha256": "docs/governance/phase_i/PHASE_I_I3_A0_TPEX_DEALER_SELL_ADJUDICATION_V1.json",
    "p1_record_sha256": "docs/governance/phase_i/PHASE_I_I3_A0_P1_TPEX_DEALER_SELL_ADJUDICATION_HARNESS_2026-10-01.json",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_reviewed_authority_chain() -> dict[str, Any]:
    """Load only the repository's single reviewed chain and verify its anchors."""
    if AUTHORITY_PATH.resolve() != (ROOT / "docs/governance/phase_i/PHASE_I_I3_A0_FUTURE_ATTEMPT_AUTHORITY_CHAIN_V1.json").resolve():
        raise ValueError("authority_chain_path_not_canonical")
    chain = json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))
    if chain.get("schema_version") != "phase_i_i3_a0_future_attempt_authority_chain.v1":
        raise ValueError("authority_chain_schema_invalid")
    if chain.get("authority_chain_status") != "REVIEWED_FIXED_HISTORICAL_ANCHORS":
        raise ValueError("authority_chain_not_reviewed")
    for key, expected in ANCHOR_FIELDS.items():
        if chain.get(key) != expected:
            raise ValueError(f"authority_chain_anchor_mismatch:{key}")
        if _sha(ROOT / HASHED_PATHS[key]) != expected:
            raise ValueError(f"historical_anchor_hash_mismatch:{key}")
    erratum_path = ROOT / "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_2_PROVENANCE_ERRATUM_2026-10-02.json"
    attempt2_path = ROOT / "docs/governance/phase_i/PHASE_I_I3_A0_ATTEMPT_2_SOURCE_TIMING_SYMMETRY_REPROBE_2026-10-01.json"
    if chain.get("attempt_2_record_sha256") != _sha(attempt2_path):
        raise ValueError("attempt2_record_anchor_mismatch")
    if chain.get("attempt_2_provenance_erratum_sha256") != _sha(erratum_path):
        raise ValueError("attempt2_erratum_anchor_mismatch")
    return chain


def validate_reservation(reservation: dict[str, Any], chain: dict[str, Any] | None = None) -> None:
    fixed = load_reviewed_authority_chain()
    if chain is not None and chain != fixed:
        raise ValueError("unreviewed_authority_chain")
    for key, expected in ANCHOR_FIELDS.items():
        if reservation.get(key) != expected:
            raise ValueError(f"reservation_anchor_mismatch:{key}")


def validate_consumed_latch(latch: dict[str, Any], chain: dict[str, Any] | None = None) -> None:
    fixed = load_reviewed_authority_chain()
    if chain is not None and chain != fixed:
        raise ValueError("unreviewed_authority_chain")
    for key, expected in ANCHOR_FIELDS.items():
        if latch.get(key) != expected:
            raise ValueError(f"consumed_anchor_mismatch:{key}")


def build_reservation(*, owner_authority: str, starting_main: str, branch: str,
                      branch_head: str, tree: str, max_gets: dict[str, int]) -> dict[str, Any]:
    chain = load_reviewed_authority_chain()
    value = {
        "schema_version": "phase_i_i3_a0_future_attempt_reservation.v1",
        "owner_authority": owner_authority, "starting_main": starting_main,
        "starting_branch": branch, "starting_branch_head": branch_head,
        "starting_tree": tree, "reserved": True, "consumed": False,
        "network_budget": dict(max_gets),
    }
    value.update({key: chain[key] for key in ANCHOR_FIELDS})
    validate_reservation(value, chain)
    return value


def build_consumed_latch(reservation: dict[str, Any], *, consumed_at: str) -> dict[str, Any]:
    chain = load_reviewed_authority_chain()
    validate_reservation(reservation, chain)
    value = {
        "schema_version": "phase_i_i3_a0_future_attempt_consumed.v1",
        "owner_authority": reservation["owner_authority"],
        "starting_main": reservation["starting_main"],
        "starting_branch": reservation["starting_branch"],
        "starting_branch_head": reservation["starting_branch_head"],
        "starting_tree": reservation["starting_tree"],
        "reserved": True, "consumed": True,
        "consumed_before_first_http_attempt": True, "consumed_at": consumed_at,
        "network_budget": dict(reservation["network_budget"]),
    }
    value.update({key: chain[key] for key in ANCHOR_FIELDS})
    validate_consumed_latch(value, chain)
    return value
