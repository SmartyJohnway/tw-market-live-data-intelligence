"""Strict validator for the network-free Attempt #5-R0 bundle contract."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_REAL_AGENT_ATTEMPT_5_R0_CODEX_RUNTIME_BUNDLE_CONTRACT_2026-10-12.json"


def _no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON member name: {key}")
        result[key] = value
    return result


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicates)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate(record: dict[str, Any] | None = None) -> dict[str, Any]:
    from scripts.phase_j_attempt5_runtime_bundle import (
        BUNDLE_ROOT, EXPECTED_BUNDLE_INVENTORY_SHA256, EXPECTED_FILE_COUNT,
        EXPECTED_TOTAL_SIZE, EXPECTED_VERSION, ROOT as REPO_ROOT,
        build_launch_contract, canonical_sha256, inventory_sha256,
        verify_bundle, verify_source_target_equivalence,
    )

    if REPO_ROOT != ROOT:
        raise ValueError("validator repository root mismatch")
    record = record if record is not None else _load(RECORD)
    if record.get("schema_version") != "phase_j_attempt5_r0_codex_runtime_bundle_acceptance.v1":
        raise ValueError("Attempt #5-R0 governance schema mismatch")
    authority = record["authority"]
    if authority != {
        "starting_head": "083d636d7315372dd0c6defb4f2bdc398f1155ed",
        "starting_tree": "03f312ef67ce44714ddd31cd177016baf629af1a",
        "branch": "phase-j/j-b04-a5-bounded-live-source-acceptance",
        "pr_number": 326,
        "pr_state": "OPEN_DRAFT_UNMERGED",
        "prior_attempt4_review": "5488441715",
        "prior_attempt4_disposition": "PHASE_J_REAL_AGENT_ATTEMPT_4_HARD_BLOCK_CODE_MODE_HOST_UNAVAILABLE = INDEPENDENTLY VERIFIED",
    }:
        raise ValueError("starting authority or Attempt #4 review mismatch")

    source_manifest = record["source_bundle"]["entries"]
    target_manifest = record["target_bundle"]["entries"]
    if source_manifest != target_manifest:
        raise ValueError("source and target inventory manifest entries differ")
    if inventory_sha256(source_manifest) != EXPECTED_BUNDLE_INVENTORY_SHA256:
        raise ValueError("committed bundle manifest aggregate hash mismatch")
    if len(source_manifest) != EXPECTED_FILE_COUNT or sum(e["size"] for e in source_manifest) != EXPECTED_TOTAL_SIZE:
        raise ValueError("committed bundle manifest size/count mismatch")
    copied = verify_source_target_equivalence(record["source_bundle"]["root"], BUNDLE_ROOT)
    if copied["source_entries"] != source_manifest or copied["target_entries"] != target_manifest:
        raise ValueError("live source/target inventory differs from committed manifest")

    contract = record["launch_contract"]["contract"]
    from scripts.phase_j_attempt5_runtime_bundle import validate_launch_contract
    validate_launch_contract(contract)
    if canonical_sha256(contract) != record["launch_contract"]["canonical_sha256"]:
        raise ValueError("Attempt #5 launch-contract canonical hash mismatch")
    rebuilt_contract = build_launch_contract()
    if rebuilt_contract != contract:
        raise ValueError("rebuilt full-bundle contract differs from committed contract")
    actual_identity = verify_bundle(
        root=BUNDLE_ROOT, expected_root=BUNDLE_ROOT, expected_entries=target_manifest,
        expected_inventory_sha256=EXPECTED_BUNDLE_INVENTORY_SHA256,
        expected_file_count=EXPECTED_FILE_COUNT, expected_total_size=EXPECTED_TOTAL_SIZE,
        expected_version=EXPECTED_VERSION,
    )
    if actual_identity != record["bundle_identity"] or actual_identity != contract["codex_runtime_bundle_identity"]:
        raise ValueError("runtime identity differs from committed bundle authority")

    probe = record["mcp_preflight"]
    log = ROOT / probe["event_log_artifact"]
    if _sha(log) != probe["event_log_sha256"]:
        raise ValueError("MCP preflight event log hash mismatch")
    events = [_load_event(line) for line in log.read_text(encoding="utf-8").splitlines() if line]
    if [e.get("event") for e in events] != ["initialize_request", "initialize_result", "tools_list", "proxy_exit"]:
        raise ValueError("MCP preflight event sequence is not initialize/tools/list only")
    tool_event = events[2]
    if tool_event.get("count") != 6 or tool_event.get("exact_six") is not True:
        raise ValueError("MCP preflight did not prove exact six-tool discovery")
    if tool_event.get("names") != contract["expected_tools"]:
        raise ValueError("MCP preflight tool inventory differs from contract")
    if events[3].get("tool_call_sequence") != [] or events[3].get("blocked_calls") != 0:
        raise ValueError("semantic MCP calls occurred during R0")
    if probe.get("semantic_calls") != 0:
        raise ValueError("semantic MCP calls occurred during R0")
    if record["local_service_preflight"] != {
        "health": "healthy", "service_contract_version": "unified_market_evidence_local_service.v2",
        "capability_count": 14, "market_execution": 0, "stopped_after_probe": True,
    }:
        raise ValueError("Local Service preflight facts differ from required contract")

    for artifact in record["codex_parser_proof"]["raw_artifacts"]:
        if _sha(ROOT / artifact["path"]) != artifact["sha256"]:
            raise ValueError(f"Codex parser evidence artifact hash mismatch: {artifact['path']}")

    for item in record["immutable_historical_files"]:
        if _sha(ROOT / item["path"]) != item["sha256"]:
            raise ValueError(f"immutable Attempt #3/#4 evidence changed: {item['path']}")
    if record["attempt4_status"] != {
        "terminal": True,
        "disposition": "PHASE_J_REAL_AGENT_ATTEMPT_4_HARD_BLOCK_CODE_MODE_HOST_UNAVAILABLE",
        "unused_slots_not_transferable": True,
        "slot_02_03_used": False,
    }:
        raise ValueError("Attempt #4 terminal/slot non-transfer semantics changed")

    from scripts.validate_phase_j_attempt3_r1_mcp_attachment import validate as validate_retained_package
    validate_retained_package()
    if any(record["boundaries"].values()):
        raise ValueError("Attempt #5-R0 boundary counter is nonzero")
    if record["attempt5_state"] != {"slots_reserved": 0, "slots_launched": 0, "maximum_slots": 3}:
        raise ValueError("Attempt #5 R0 must leave all slots unused")
    if record["derived_state"] != {
        "remaining_obligations": ["real_agent_layer"], "phase_j": "STARTED",
        "roadmap_phase_j": "UNCHECKED", "phase_k": "NOT_STARTED",
        "pr_state": "OPEN_DRAFT_UNMERGED", "closure_credit": False,
    }:
        raise ValueError("R0 must not change Phase-J derived state")
    return {
        "status": "PASS", "source_target_file_entries": EXPECTED_FILE_COUNT,
        "bundle_inventory_sha256": EXPECTED_BUNDLE_INVENTORY_SHA256,
        "codex_runtime_bundle": "PASS", "launch_contract": "PASS",
        "mcp_initialize_tools_list": "PASS", "semantic_mcp_calls": 0,
        "attempt5_slots_reserved": 0, "attempt5_slots_launched": 0,
    }


def _load_event(line: str) -> dict[str, Any]:
    return json.loads(line, object_pairs_hook=_no_duplicates)


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
