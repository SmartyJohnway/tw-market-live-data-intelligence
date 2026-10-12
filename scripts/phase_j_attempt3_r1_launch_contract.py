"""Build and validate the network-free Phase-J formal-session MCP launch contract."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

CONTROL_ID = "umea-v1-64317f4f3435611c2bb5"
SERVER_NAME = "phase_j_witness"
PROXY_RELATIVE = Path("scripts/phase_j_real_agent_attempt2_proxy.py")
PROMPT = (
    "Inspect the existing governed stored result for the supplied control package and its AI handoff using only the available governed stored-result tools. "
    "Explain what the evidence establishes about the observation's currentness and how it may safely be interpreted. "
    "Do not obtain fresh market data. Do not make a trading recommendation or trading signal. "
    "Base the answer only on the governed stored result and handoff you retrieve."
)
EXPECTED_TOOLS = [
    "market_describe_capabilities", "market_validate_request", "market_preview_request",
    "market_read_result", "market_export_ai_handoff", "market_fetch_evidence",
]


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def _toml_value(value: Any) -> str:
    if isinstance(value, str):
        return _toml_string(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ",".join(_toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(f"{key}={_toml_value(value[key])}" for key in sorted(value)) + "}"
    raise TypeError(f"unsupported TOML override value: {type(value).__name__}")


def config_override(server: dict[str, Any]) -> str:
    payload = {key: value for key, value in server.items() if key != "name"}
    return "mcp_servers." + SERVER_NAME + "=" + _toml_value(payload)


def build_contract(
    *, codex_executable: str, codex_version: str, python_executable: str,
    repository_cwd: str, runtime_root: str, service_url: str,
    prompt_path: str, witness_log_path: str, codex_events_path: str,
    stderr_path: str, final_output_path: str, startup_timeout_sec: int = 30,
) -> dict[str, Any]:
    repo = Path(repository_cwd).resolve()
    proxy = (repo / PROXY_RELATIVE).resolve()
    paths = [codex_executable, python_executable, str(repo), str(proxy), runtime_root,
             prompt_path, witness_log_path, codex_events_path, stderr_path, final_output_path]
    if any(not Path(item).is_absolute() for item in paths):
        raise ValueError("all launch contract paths must be absolute")
    if not re.fullmatch(r"umea-v1-[0-9a-f]{20}", CONTROL_ID):
        raise ValueError("invalid fixed control package identity")
    if Path(witness_log_path).exists():
        raise ValueError("witness log path must be unused")
    argv = [str(proxy), "--log", witness_log_path, "--control-package-id", CONTROL_ID]
    server = {
        "command": python_executable,
        "args": argv,
        "cwd": str(repo),
        "env": {
            "UNIFIED_MARKET_EVIDENCE_SERVICE_URL": service_url,
            "PHASEJ_WITNESS_PROXY_LOG": witness_log_path,
        },
        "enabled": True,
        "required": True,
        "startup_timeout_sec": startup_timeout_sec,
    }
    override = config_override(server)
    return {
        "schema_version": "phase_j_real_agent_attempt_3_r1_launch_contract.v1",
        "codex": {
            "executable": codex_executable,
            "version": codex_version,
            "formal_command": [
                codex_executable, "exec", "--ignore-user-config", "--ephemeral", "--json",
                "--output-last-message", final_output_path, "--cd", str(repo),
                "-c", override, "-",
            ],
            "ignore_user_config": True,
            "configuration_overrides": [override],
            "profile_identity": "EXPLICIT_COMMAND_LINE_MCP_OVERRIDE_NO_PROFILE",
            "json_event_output_path": codex_events_path,
            "stderr_path": stderr_path,
            "final_output_path": final_output_path,
            "stdin_prompt_path": prompt_path,
        },
        "repository_cwd": str(repo),
        "mcp_server": {"name": SERVER_NAME, **server},
        "proxy": {
            "python_executable": python_executable,
            "script_absolute_path": str(proxy),
            "argv": argv,
            "cwd": str(repo),
        },
        "control_package_id": CONTROL_ID,
        "local_service_url": service_url,
        "runtime_root": runtime_root,
        "prompt_artifact_path": prompt_path,
        "prompt_sha256": sha256_bytes(PROMPT.encode("utf-8")),
        "semantic_call_policy": {
            "maximum_calls": 2,
            "ordered_tools": ["market_read_result", "market_export_ai_handoff"],
            "exact_arguments": {"control_package_id": CONTROL_ID},
        },
        "expected_tools": EXPECTED_TOOLS,
        "provider_launch_authorized_in_this_tranche": False,
        "prelaunch_gates": {
            "formal_session_mcp_configuration_verified": True,
            "required_mcp_server": SERVER_NAME,
            "local_service_health_required": True,
            "exact_six_tool_probe_required": True,
            "witness_log_path_must_not_exist": True,
            "provider_session_launched_in_this_tranche": False,
        },
    }


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "phase_j_real_agent_attempt_3_r1_launch_contract.v1":
        raise ValueError("contract schema mismatch")
    codex = contract["codex"]
    server = contract["mcp_server"]
    proxy = contract["proxy"]
    if codex.get("ignore_user_config") is not True:
        raise ValueError("formal invocation must ignore user MCP configuration")
    if server.get("name") != SERVER_NAME or server.get("required") is not True or server.get("enabled") is not True:
        raise ValueError("required witness server definition missing")
    if server.get("command") != proxy.get("python_executable"):
        raise ValueError("proxy interpreter mismatch")
    if not Path(server["command"]).is_absolute() or not Path(codex["executable"]).is_absolute():
        raise ValueError("Codex and proxy interpreter paths must be absolute")
    if server.get("cwd") != contract.get("repository_cwd") or proxy.get("cwd") != contract.get("repository_cwd"):
        raise ValueError("proxy cwd mismatch")
    if server.get("args") != proxy.get("argv"):
        raise ValueError("proxy argv mismatch")
    expected_proxy = str((Path(contract["repository_cwd"]) / PROXY_RELATIVE).resolve())
    if proxy.get("script_absolute_path") != expected_proxy or server["args"][0] != expected_proxy:
        raise ValueError("proxy must resolve to the accepted repository script")
    expected = [proxy["script_absolute_path"], "--log", contract["mcp_server"]["env"]["PHASEJ_WITNESS_PROXY_LOG"],
                "--control-package-id", contract["control_package_id"]]
    if server["args"] != expected:
        raise ValueError("exact proxy command/package/log binding mismatch")
    if not re.fullmatch(r"umea-v1-[0-9a-f]{20}", contract.get("control_package_id", "")):
        raise ValueError("invalid control package id")
    if server["startup_timeout_sec"] < 1:
        raise ValueError("invalid startup timeout")
    if Path(server["env"]["PHASEJ_WITNESS_PROXY_LOG"]).exists():
        raise ValueError("witness log path already exists")
    if "stale" in Path(contract["prompt_artifact_path"]).name.lower():
        raise ValueError("prompt path must not disclose expected semantic outcome")
    formal = codex["formal_command"]
    if "--ignore-user-config" not in formal or "-c" not in formal or "-" not in formal:
        raise ValueError("formal command does not attach the explicit MCP override")
    if codex["configuration_overrides"] != [config_override(server)]:
        raise ValueError("Codex override differs from validated MCP server definition")
