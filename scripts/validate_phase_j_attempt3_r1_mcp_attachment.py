"""Validate the network-free Attempt #3-R1 MCP attachment contract evidence."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_REAL_AGENT_ATTEMPT_3_R1_MCP_ATTACHMENT_CONTRACT_2026-10-12.json"


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON member name: {key}")
        result[key] = value
    return result


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs_no_duplicates)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate(record: dict[str, Any] | None = None) -> dict[str, Any]:
    record = record if record is not None else _load(RECORD)
    from scripts.phase_j_attempt3_r1_launch_contract import validate_contract

    contract = record["launch_contract"]
    validate_contract(contract)
    if _canonical_sha(contract) != record["launch_contract_sha256"]:
        raise ValueError("launch contract canonical SHA-256 mismatch")
    prompt = ROOT / record["prompt"]["repository_path"]
    if _sha(prompt) != record["prompt"]["sha256"]:
        raise ValueError("neutral prompt SHA-256 mismatch")
    if _sha(prompt) != contract["prompt_sha256"]:
        raise ValueError("prompt and launch contract hash differ")

    dry = record["dry_preflight"]
    probe_proof = dry["proxy_stdio_probe"]
    probe_log = Path(probe_proof["probe_log_absolute_path"])
    if _sha(probe_log) != probe_proof["proxy_probe_log_sha256"]:
        raise ValueError("proxy initialize/tools-list log hash mismatch")
    events = [_load_line(line) for line in probe_log.read_text(encoding="utf-8").splitlines()]
    names = [event.get("event") for event in events]
    if names != ["initialize_request", "initialize_result", "tools_list", "proxy_exit"]:
        raise ValueError("unexpected proxy preflight event sequence")
    if events[2].get("exact_six") is not True or events[2].get("count") != 6:
        raise ValueError("exact six-tool discovery failed")
    if events[3].get("tool_call_sequence") != [] or events[3].get("blocked_calls") != 0:
        raise ValueError("semantic MCP calls occurred during preflight")
    if dry["local_service"]["health"] != "PASS" or dry["local_service"]["capability_count"] != 14:
        raise ValueError("Local Service preflight failed")
    if dry["codex_config_inspection"]["mcp_list_exit"] != 0 or dry["codex_config_inspection"]["mcp_get_exit"] != 0:
        raise ValueError("Codex config parser/list/get proof failed")
    if dry["codex_config_inspection"]["effective_server_count"] != 1:
        raise ValueError("isolated Codex config included unexpected MCP servers")

    immutable = record["immutable_authorities"]
    for item in immutable["files"]:
        if _sha(ROOT / item["path"]) != item["sha256"]:
            raise ValueError(f"immutable historical authority changed: {item['path']}")
    inventory = immutable["runtime_package"]
    runtime = Path(inventory["runtime_root"])
    package = runtime / "control" / inventory["control_package_id"]
    actual_files = []
    for path in sorted(candidate for candidate in package.rglob("*") if candidate.is_file()):
        actual_files.append({
            "byte_size": path.stat().st_size,
            "relative_path": path.relative_to(package).as_posix(),
            "sha256": _sha(path),
        })
    if len(actual_files) != inventory["file_count"] or actual_files != inventory["files"]:
        raise ValueError("retained R4-R2 package file inventory differs")
    if _canonical_sha(actual_files) != inventory["inventory_sha256"]:
        raise ValueError("retained R4-R2 package inventory hash differs")

    expected_zero = {
        "provider_inference": 0, "provider_sessions_launched": 0,
        "real_agent_sessions": 0, "semantic_mcp_calls": 0,
        "j1_21_executions": 0, "source_fixture_invocation_delta": 0,
        "market_GET": 0, "market_HEAD": 0, "market_POST": 0,
        "browser_use": 0, "firecrawl": 0,
        "security_master_acquisition": 0, "security_master_mutation": 0,
        "production_code_changes": 0, "public_schema_changes": 0,
        "mcp_tool_count_change": 0,
    }
    if record["boundaries"] != expected_zero:
        raise ValueError("R3-R1 boundary counters are not all zero")
    if record["derived_state"]["remaining_obligations"] != ["real_agent_layer"]:
        raise ValueError("R3-R1 must not award real-agent closure credit")
    return {"status": "PASS", "duplicate_json_member_names": 0, "runtime_package_files": len(actual_files)}


def _load_line(line: str) -> dict[str, Any]:
    return json.loads(line, object_pairs_hook=_pairs_no_duplicates)


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
