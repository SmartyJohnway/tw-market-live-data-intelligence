"""Pinned Codex runtime and bounded-slot contract for Phase-J Attempt #4.

This module prepares and validates launch material only. It never starts a
Codex provider session or invokes a semantic MCP tool.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = Path(r"D:\Codex-Workspace\runtime\tw-market-live-data-intelligence\phase-j-real-agent-r4-r2")
PACKAGE_ROOT = RUNTIME_ROOT / "j1-21-preparation-2026-10-12"
ATTEMPT_ROOT = RUNTIME_ROOT / "attempt4"
PINNED_CODEX = RUNTIME_ROOT / "codex-pinned" / "0.160.1" / "codex.exe"
PINNED_IDENTITY = {
    "absolute_executable_path": str(PINNED_CODEX),
    "observed_version": "codex-cli 0.160.1",
    "sha256": "9e7c59c05cc1ce5677b1f94e835b2ac038ca3be14504e78d558eacdb0ea3f55d",
    "byte_size": 326875440,
}
PYTHON = Path(r"C:\Users\weitang\AppData\Local\Programs\Python\Python313\python.exe")
PROXY = ROOT / "scripts" / "phase_j_real_agent_attempt2_proxy.py"
CONTROL_ID = "umea-v1-64317f4f3435611c2bb5"
SERVICE_URL = "http://127.0.0.1:18264"
PROMPT_PATH = ROOT / "docs/governance/phase_j/PHASE_J_REAL_AGENT_ATTEMPT_3_R1_NEUTRAL_PROMPT_2026-10-12.txt"
PROMPT_SHA256 = "8ee5459c7217ff34d091385f588d8b53794a1053ace2a44e5b262e4f6757621c"
MAXIMUM_SLOTS = 3
SERVER_NAME = "phase_j_witness"
TOOLS = [
    "market_describe_capabilities", "market_validate_request", "market_preview_request",
    "market_read_result", "market_export_ai_handoff", "market_fetch_evidence",
]
EXPECTED_PACKAGE_INVENTORY = "caa4b43c67b235ce104c0277b1493031466d39159591e87f56c8765ed0c09096"
FROZEN_LAUNCH_CONTRACT_SHA256 = "52a97e0362237cb93eca3733b7fdb1f8a11cdcf66a757b0fdd736623e1a78152"


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_version(executable: str) -> tuple[int, str]:
    completed = subprocess.run(
        [executable, "--version"], capture_output=True, text=True, encoding="utf-8",
        errors="strict", check=False, timeout=30,
    )
    return completed.returncode, (completed.stdout + completed.stderr).strip()


def verify_codex_runtime_identity(
    identity: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Re-measure the pinned executable; caller-provided version is never authority."""
    expected = PINNED_IDENTITY
    candidate = identity or expected
    path_text = candidate.get("absolute_executable_path")
    if not isinstance(path_text, str) or not Path(path_text).is_absolute():
        raise ValueError("Codex executable path must be absolute")
    resolved = str(Path(path_text).resolve(strict=True))
    frozen_path = str(Path(expected["absolute_executable_path"]).resolve(strict=True))
    if resolved.casefold() != frozen_path.casefold():
        raise ValueError("Codex executable path differs from pinned authority")
    executable = Path(resolved)
    size = executable.stat().st_size
    digest = _sha_file(executable)
    if size != expected["byte_size"]:
        raise ValueError("Codex executable byte size differs from pinned authority")
    if digest != expected["sha256"]:
        raise ValueError("Codex executable SHA-256 differs from pinned authority")
    code, version = _run_version(resolved)
    if code != 0:
        raise ValueError("pinned Codex --version returned non-zero")
    if version != expected["observed_version"]:
        raise ValueError("pinned Codex --version output differs from pinned authority")
    if executable.stat().st_size != size or _sha_file(executable) != digest:
        raise ValueError("Codex executable changed while runtime identity was being verified")
    measured = {
        "absolute_executable_path": resolved,
        "observed_version": version,
        "sha256": digest,
        "byte_size": size,
    }
    if candidate != measured:
        raise ValueError("contract Codex runtime identity differs from measured executable")
    return measured


def slot_paths(slot: int, *, root: Path | None = None) -> dict[str, str]:
    if isinstance(slot, bool) or not isinstance(slot, int) or not 1 <= slot <= MAXIMUM_SLOTS:
        raise ValueError("slot number must be between 1 and 3")
    root = ATTEMPT_ROOT if root is None else root
    directory = root / f"attempt4-slot-{slot:02d}"
    return {
        "directory": str(directory),
        "witness_events": str(directory / "witness-events.jsonl"),
        "codex_events": str(directory / "codex-events.jsonl"),
        "codex_stderr": str(directory / "codex-stderr.txt"),
        "agent_final": str(directory / "agent-final.txt"),
        "slot_receipt": str(directory / "slot-receipt.json"),
        "reservation": str(directory / "slot-reserved.json"),
    }


def _toml(value: Any) -> str:
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ",".join(_toml(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{" + ",".join(f"{key}={_toml(value[key])}" for key in sorted(value)) + "}"
    raise TypeError(type(value).__name__)


def derive_slot_contract(contract: dict[str, Any], slot: int, *, root: Path | None = None) -> dict[str, Any]:
    validate_contract(contract)
    root = ATTEMPT_ROOT if root is None else root
    paths = slot_paths(slot, root=root)
    if Path(paths["witness_events"]).exists():
        raise ValueError("slot witness log already exists")
    server = dict(contract["mcp_server_template"])
    server["args"] = [str(PROXY), "--log", paths["witness_events"], "--control-package-id", CONTROL_ID]
    server["env"] = {
        "PHASEJ_WITNESS_PROXY_LOG": paths["witness_events"],
        "UNIFIED_MARKET_EVIDENCE_SERVICE_URL": SERVICE_URL,
    }
    override = "mcp_servers." + SERVER_NAME + "=" + _toml(server)
    command = [
        PINNED_IDENTITY["absolute_executable_path"], "exec", "--ignore-user-config", "--ephemeral", "--json",
        "--output-last-message", paths["agent_final"], "--cd", str(ROOT), "-c", override, "-",
    ]
    return {
        "slot": slot,
        "paths": paths,
        "mcp_server": {"name": SERVER_NAME, **server},
        "configuration_override": override,
        "formal_command": command,
        "stdout_path": paths["codex_events"],
        "stderr_path": paths["codex_stderr"],
        "stdin_prompt_path": str(PROMPT_PATH),
    }


def build_contract() -> dict[str, Any]:
    identity = verify_codex_runtime_identity()
    prompt_bytes = PROMPT_PATH.read_bytes()
    if hashlib.sha256(prompt_bytes).hexdigest() != PROMPT_SHA256:
        raise ValueError("neutral prompt bytes differ from frozen authority")
    template = {
        "command": str(PYTHON),
        "args": [str(PROXY), "--log", "<SLOT>/witness-events.jsonl", "--control-package-id", CONTROL_ID],
        "cwd": str(ROOT),
        "env": {
            "PHASEJ_WITNESS_PROXY_LOG": "<SLOT>/witness-events.jsonl",
            "UNIFIED_MARKET_EVIDENCE_SERVICE_URL": SERVICE_URL,
        },
        "enabled": True,
        "required": True,
        "startup_timeout_sec": 30,
    }
    return {
        "schema_version": "phase_j_real_agent_attempt_4_launch_contract.v2",
        "codex_runtime_identity": identity,
        "formal_cli_grammar": ["exec", "--ignore-user-config", "--ephemeral", "--json", "--output-last-message", "--cd", "-c", "-"],
        "ignore_user_config": True,
        "repository_cwd": str(ROOT),
        "profile_identity": "EXPLICIT_COMMAND_LINE_MCP_OVERRIDE_NO_PROFILE",
        "mcp_server_template": template,
        "python_executable": str(PYTHON),
        "proxy_script_absolute_path": str(PROXY),
        "control_package_id": CONTROL_ID,
        "local_service_url": SERVICE_URL,
        "runtime_root": str(RUNTIME_ROOT),
        "package_root": str(PACKAGE_ROOT),
        "attempt_evidence_root": str(ATTEMPT_ROOT),
        "package_inventory_sha256": EXPECTED_PACKAGE_INVENTORY,
        "prompt_path": str(PROMPT_PATH),
        "prompt_sha256": PROMPT_SHA256,
        "maximum_slots": MAXIMUM_SLOTS,
        "slot_path_template": "attempt4-slot-{slot:02d}/{witness-events.jsonl,codex-events.jsonl,codex-stderr.txt,agent-final.txt,slot-receipt.json}",
        "stdout_capture": "Codex JSONL stdout is redirected to slot codex-events.jsonl",
        "stderr_capture": "Codex stderr is redirected to slot codex-stderr.txt",
        "final_output_capture": "--output-last-message writes slot agent-final.txt",
        "witness_capture": "proxy --log writes slot witness-events.jsonl",
        "semantic_call_policy": {
            "maximum_calls": 2,
            "ordered_tools": ["market_read_result", "market_export_ai_handoff"],
            "exact_arguments": {"control_package_id": CONTROL_ID},
        },
        "expected_tools": TOOLS,
        "provider_launch_authorized_in_r0": False,
        "attempt4_slots_reserved_in_r0": 0,
        "attempt4_slots_launched_in_r0": 0,
    }


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "phase_j_real_agent_attempt_4_launch_contract.v2":
        raise ValueError("launch contract schema mismatch")
    verify_codex_runtime_identity(contract.get("codex_runtime_identity"))
    if contract.get("maximum_slots") != 3 or contract.get("ignore_user_config") is not True:
        raise ValueError("slot limit or isolated Codex config invariant failed")
    if contract.get("control_package_id") != CONTROL_ID:
        raise ValueError("wrong retained control package")
    if contract.get("repository_cwd") != str(ROOT) or contract.get("proxy_script_absolute_path") != str(PROXY):
        raise ValueError("repository or proxy path differs from reviewed authority")
    if contract.get("attempt_evidence_root") != str(ATTEMPT_ROOT):
        raise ValueError("slot evidence root differs from the Git-external Attempt #4 root")
    if contract.get("runtime_root") != str(RUNTIME_ROOT) or contract.get("package_root") != str(PACKAGE_ROOT):
        raise ValueError("runtime/package root differs from retained-package authority")
    server = contract.get("mcp_server_template", {})
    if server.get("required") is not True or server.get("enabled") is not True or server.get("startup_timeout_sec") != 30:
        raise ValueError("witness MCP must be enabled, required, and use 30 second startup timeout")
    if server.get("command") != str(PYTHON) or server.get("cwd") != str(ROOT):
        raise ValueError("witness MCP command or cwd mismatch")
    expected_args = [str(PROXY), "--log", "<SLOT>/witness-events.jsonl", "--control-package-id", CONTROL_ID]
    if server.get("args") != expected_args or server.get("env", {}).get("UNIFIED_MARKET_EVIDENCE_SERVICE_URL") != SERVICE_URL:
        raise ValueError("witness MCP proxy arguments or service URL mismatch")
    if contract.get("prompt_sha256") != PROMPT_SHA256 or hashlib.sha256(Path(contract["prompt_path"]).read_bytes()).hexdigest() != PROMPT_SHA256:
        raise ValueError("neutral prompt changed")
    if contract.get("package_inventory_sha256") != EXPECTED_PACKAGE_INVENTORY:
        raise ValueError("retained package identity changed")
    if contract.get("semantic_call_policy", {}).get("maximum_calls") != 2:
        raise ValueError("semantic call limit mismatch")


def validate_reviewed_contract(contract: dict[str, Any]) -> None:
    validate_contract(contract)
    if canonical_sha256(contract) != FROZEN_LAUNCH_CONTRACT_SHA256:
        raise ValueError("launch contract differs from exact R0-reviewed canonical hash")


def reserve_slot(
    contract: dict[str, Any], slot: int, *, now: str,
    preflight: dict[str, Any], expected_contract_sha256: str,
) -> Path:
    """Create a slot reservation only after all caller preflight gates pass."""
    validate_reviewed_contract(contract)
    actual_contract_hash = canonical_sha256(contract)
    if expected_contract_sha256 != actual_contract_hash or preflight.get("launch_contract_sha256") != actual_contract_hash:
        raise ValueError("preflight launch contract hash mismatch")
    required_gates = {
        "git_authority_verified", "retained_package_verified", "codex_runtime_verified",
        "local_service_healthy", "mcp_configuration_verified", "mcp_exact_six_probe_passed",
    }
    if any(preflight.get(gate) is not True for gate in required_gates):
        raise ValueError("slot preflight gates are incomplete")
    paths = slot_paths(slot)
    directory = Path(paths["directory"])
    directory.mkdir(parents=True, exist_ok=False)
    reservation = {
        "schema_version": "phase_j_attempt4_slot_reservation.v1",
        "slot": slot,
        "reserved_at": now,
        "launch_contract_sha256": canonical_sha256(contract),
        "control_package_id": CONTROL_ID,
        "status": "RESERVED_NOT_LAUNCHED",
    }
    Path(paths["reservation"]).write_bytes(canonical_bytes(reservation))
    return Path(paths["reservation"])


def run_reserved_slot(
    contract: dict[str, Any], slot: int, *, preflight: dict[str, Any],
    authorization_consumed: bool, prompt_bytes: bytes, popen_factory=None,
):
    """Future-only launcher: capture all streams to slot files before returning.

    R0 intentionally does not call this function. A future Owner-authorized
    attempt must reserve first and pass every preflight gate before invoking it.
    """
    import subprocess as _subprocess

    validate_reviewed_contract(contract)
    if authorization_consumed is not True:
        raise ValueError("formal provider authorization must be explicitly consumed before launch")
    expected_hash = canonical_sha256(contract)
    if preflight.get("launch_contract_sha256") != expected_hash:
        raise ValueError("preflight launch contract hash mismatch")
    required_gates = {
        "git_authority_verified", "retained_package_verified", "codex_runtime_verified",
        "local_service_healthy", "mcp_configuration_verified", "mcp_exact_six_probe_passed",
    }
    if any(preflight.get(gate) is not True for gate in required_gates):
        raise ValueError("formal launch preflight gates are incomplete")
    paths = slot_paths(slot)
    reservation_path = Path(paths["reservation"])
    if not reservation_path.is_file():
        raise ValueError("slot must be reserved before provider launch")
    reservation = json.loads(reservation_path.read_text(encoding="utf-8"))
    if reservation.get("launch_contract_sha256") != expected_hash or reservation.get("slot") != slot:
        raise ValueError("slot reservation does not match launch contract")
    slot_contract = derive_slot_contract(contract, slot)
    if hashlib.sha256(prompt_bytes).hexdigest() != PROMPT_SHA256:
        raise ValueError("formal prompt bytes differ from reviewed neutral prompt")
    for key in ("codex_events", "codex_stderr", "agent_final", "witness_events"):
        if Path(paths[key]).exists():
            raise ValueError(f"slot evidence path already exists: {key}")
    Path(paths["directory"]).mkdir(parents=True, exist_ok=True)
    Path(paths["directory"], "launch-started.json").write_bytes(canonical_bytes({
        "slot": slot, "launch_contract_sha256": expected_hash,
        "provider_launch_authorized": True, "status": "LAUNCH_STARTED",
    }))
    factory = _subprocess.Popen if popen_factory is None else popen_factory
    with open(paths["codex_events"], "wb") as stdout, open(paths["codex_stderr"], "wb") as stderr:
        process = factory(
            slot_contract["formal_command"], cwd=str(ROOT), stdin=_subprocess.PIPE,
            stdout=stdout, stderr=stderr,
        )
        process.communicate(input=prompt_bytes)
    return process.returncode


if __name__ == "__main__":
    built = build_contract()
    validate_contract(built)
    print(json.dumps({"contract": built, "canonical_sha256": canonical_sha256(built)}, ensure_ascii=False, sort_keys=True, indent=2))
