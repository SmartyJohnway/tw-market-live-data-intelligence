"""Strict offline validator for the pinned Attempt #4-R0 launch contract."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_REAL_AGENT_ATTEMPT_4_R0_PINNED_CODEX_RUNTIME_CONTRACT_2026-10-12.json"


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
    from scripts.phase_j_attempt4_r0_launch_contract import (
        CONTROL_ID, MAXIMUM_SLOTS, PINNED_IDENTITY, PROMPT_SHA256,
        canonical_sha256, validate_reviewed_contract,
    )

    record = record if record is not None else _load(RECORD)
    contract = record["launch_contract"]
    validate_reviewed_contract(contract)
    if canonical_sha256(contract) != record["launch_contract_sha256"]:
        raise ValueError("successor launch-contract canonical SHA-256 mismatch")
    if contract["codex_runtime_identity"] != PINNED_IDENTITY:
        raise ValueError("runtime identity differs from frozen pinned executable authority")
    if Path(contract["attempt_evidence_root"]).resolve() == Path(contract["package_root"]).resolve():
        raise ValueError("Attempt #4 slot evidence root must be separate from the retained package")
    if contract["maximum_slots"] != MAXIMUM_SLOTS or record["attempt4_state"] != {
        "slots_reserved": 0, "slots_launched": 0, "maximum_slots": 3,
    }:
        raise ValueError("R0 must leave every Attempt #4 slot unused")
    incident = record["test_hygiene_incident"]
    if incident.get("formal_attempt4_slot_reserved") is not False or incident.get("provider_launched") is not False:
        raise ValueError("test-only marker must not be represented as a formal Attempt #4 slot")
    if incident.get("cleanup_verified") is not True or incident.get("post_cleanup_r4_r2_inventory_validation") != "PASS_16_FILES_EXACT_SHA256":
        raise ValueError("test artifact cleanup/package restoration was not verified")
    package_root = Path(contract["package_root"])
    if any((package_root / f"attempt4-slot-{slot:02d}").exists() for slot in range(1, 4)):
        raise ValueError("formal slot evidence must remain outside the retained package root")
    if record["prompt"]["sha256"] != PROMPT_SHA256:
        raise ValueError("neutral prompt hash mismatch")
    if record["control_package_id"] != CONTROL_ID:
        raise ValueError("wrong retained package binding")
    if record["root_cause"].get("R3_R1_V1_CONTRACT_SUPERSEDED") is not True:
        raise ValueError("historical v1 contract supersession is not explicit")
    if record["root_cause"].get("classification") != "LAUNCH_CONTRACT_EXECUTABLE_VERSION_BINDING_DEFECT":
        raise ValueError("incorrect root-cause classification")
    if record["authority"].get("superseding_review_id") != "5487580175":
        raise ValueError("wrong controlling correction review")

    for item in record["immutable_historical_files"]:
        if _sha(ROOT / item["path"]) != item["sha256"]:
            raise ValueError(f"historical evidence changed: {item['path']}")

    proof = record["codex_configuration_proof"]
    if proof["list_exit_code"] != 0 or proof["get_exit_code"] != 0 or proof["effective_server_count"] != 1:
        raise ValueError("pinned Codex MCP list/get proof failed")
    listing = proof["list_servers"]
    if len(listing) != 1 or listing[0].get("name") != "phase_j_witness":
        raise ValueError("isolated Codex config includes unexpected MCP servers")
    configured = listing[0]
    server = contract["mcp_server_template"]
    if configured.get("enabled") is not True or configured.get("startup_timeout_sec") != 30:
        raise ValueError("pinned Codex MCP list output differs from contract")
    transport = configured.get("transport", {})
    if transport.get("command") != server["command"] or transport.get("args") != record["parser_probe"]["expected_args"]:
        raise ValueError("Codex MCP parser readback command/args differ")
    if transport.get("cwd") != server["cwd"]:
        raise ValueError("Codex MCP parser readback cwd differs")
    if proof["required_input_value"] is not True:
        raise ValueError("contract input must set required=true")

    local = record["local_service_preflight"]
    if local != {
        "health": "healthy", "service_contract_version": "unified_market_evidence_local_service.v2",
        "capability_catalog_schema_version": "unified_market_evidence_capability_catalog.v3",
        "capability_count": 14, "market_execution": 0, "stopped_after_probe": True,
    }:
        raise ValueError("Local Service readiness proof does not match accepted v2/14-tool surface")

    probe = record["proxy_stdio_probe"]
    log = Path(probe["log_path"])
    if _sha(log) != probe["log_sha256"]:
        raise ValueError("stdio probe log hash mismatch")
    events = [_load_line(line) for line in log.read_text(encoding="utf-8").splitlines()]
    if [item.get("event") for item in events] != ["initialize_request", "initialize_result", "tools_list", "proxy_exit"]:
        raise ValueError("unexpected stdio probe event sequence")
    if events[2].get("count") != 6 or events[2].get("exact_six") is not True:
        raise ValueError("MCP tools/list did not return the exact six-tool surface")
    if events[3].get("tool_call_sequence") != [] or events[3].get("blocked_calls") != 0:
        raise ValueError("semantic MCP call occurred during R0 probe")

    boundaries = record["boundaries"]
    if any(value != 0 for value in boundaries.values()):
        raise ValueError("R0 boundaries must all remain zero")
    if record["derived_state"] != {
        "remaining_obligations": ["real_agent_layer"], "phase_j": "STARTED",
        "roadmap_phase_j": "UNCHECKED", "phase_k": "NOT_STARTED",
        "pr_state": "OPEN_DRAFT_UNMERGED", "closure_credit": False,
    }:
        raise ValueError("R0 must not change Phase-J derived state")

    # Re-run the prior strict evidence validator to protect Attempt #3/R4-R2.
    from scripts.validate_phase_j_attempt3_r1_mcp_attachment import validate as validate_r3_r1
    validate_r3_r1()
    return {
        "status": "PASS", "duplicate_json_member_names": 0,
        "runtime_identity": "PASS", "codex_config_parser": "PASS",
        "mcp_initialize_tools_list": "PASS", "semantic_mcp_calls": 0,
        "attempt4_slots_reserved": 0, "attempt4_slots_launched": 0,
    }


def _load_line(line: str) -> dict[str, Any]:
    return json.loads(line, object_pairs_hook=_no_duplicates)


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
