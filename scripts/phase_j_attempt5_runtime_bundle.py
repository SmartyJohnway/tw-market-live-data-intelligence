"""Acceptance-only full Codex runtime bundle and Attempt #5 launch contract."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = Path(r"D:\Codex-Workspace\runtime\tw-market-live-data-intelligence\phase-j-real-agent-r4-r2")
SOURCE_ROOT = Path(r"C:\Users\weitang\AppData\Roaming\npm\node_modules\@openai\codex\node_modules\@openai\codex-win32-x64\vendor\x86_64-pc-windows-msvc")
BUNDLE_ROOT = RUNTIME_ROOT / "codex-pinned" / "0.160.1-bundle"
ATTEMPT_ROOT = RUNTIME_ROOT / "attempt5"
EXPECTED_BUNDLE_INVENTORY_SHA256 = "5e0e4b9752aa06cc0d8609168cae658efcd1c544160272f8a64f3a1c1ea08629"
EXPECTED_FILE_COUNT = 45
EXPECTED_TOTAL_SIZE = 450588539
EXPECTED_VERSION = "codex-cli 0.160.1"
CONTROL_ID = "umea-v1-64317f4f3435611c2bb5"
PACKAGE_INVENTORY_SHA256 = "caa4b43c67b235ce104c0277b1493031466d39159591e87f56c8765ed0c09096"
RESULT_ID = "umeresult-v3-63bd91d7e710438dbdd6"
RESULT_SHA256 = "d6737011bdf12e3893bbc0d6c54d98a4a472c7ebd34692276e84b250b87b0db9"
AUDIT_ID = "umeap-v3-9063d2331c6cc7718a1e"
AUDIT_SHA256 = "490145920801afd443ff8f41bd9dcea97985bc362c726c89f1037fc1f047427d"
HANDOFF_SHA256 = "b1fa8e28ef25f4f369904f6d8bf17047e3adff46d1c497a8f323396384bd8e57"
PYTHON = Path(r"C:\Users\weitang\AppData\Local\Programs\Python\Python313\python.exe")
PROXY = ROOT / "scripts" / "phase_j_real_agent_attempt2_proxy.py"
SERVICE_URL = "http://127.0.0.1:18264"
PROMPT_PATH = ROOT / "docs/governance/phase_j/PHASE_J_REAL_AGENT_ATTEMPT_3_R1_NEUTRAL_PROMPT_2026-10-12.txt"
PROMPT_SHA256 = "8ee5459c7217ff34d091385f588d8b53794a1053ace2a44e5b262e4f6757621c"
MAXIMUM_SLOTS = 3
TOOLS = [
    "market_describe_capabilities", "market_export_ai_handoff", "market_fetch_evidence",
    "market_preview_request", "market_read_result", "market_validate_request",
]
SEMANTIC_TOOLS = ["market_read_result", "market_export_ai_handoff"]
KEY_FILE_IDENTITIES = {
    "bin/codex.exe": (326875440, "9e7c59c05cc1ce5677b1f94e835b2ac038ca3be14504e78d558eacdb0ea3f55d"),
    "bin/codex-code-mode-host.exe": (74669360, "b905b5169bd758dbe3c31ca22c22ad0c24df0047ba7ae32652c706d3ac3ba78d"),
    "codex-resources/codex-command-runner.exe": (8207152, "dd2309aa856f9a951c43e88f91200887e0054897f3c866983439b69036a95774"),
    "codex-resources/codex-windows-sandbox-setup.exe": (17684272, "aeddd768276e4d0123154d7ee65876ec92b1cf8a0481c4d9c5cd8b31f2de6bf5"),
    "codex-package.json": (215, "07043ad1bfec6934b83af0cb50308ba452b06f4341ca2b2fdb9a80d4c621bdb8"),
    "codex-path/rg.exe": (4218880, "14231169855ec5205cf5a1b6f1db358ff4aed4247c86b69ce8aae647c77f6680"),
}


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def file_sha256(path: Path | str) -> str:
    path = Path(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(root: Path) -> list[dict[str, Any]]:
    root = Path(root).resolve(strict=True)
    entries: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"runtime bundle must not contain symlinks: {path}")
        if path.is_file():
            entries.append({
                "path": path.relative_to(root).as_posix(),
                "size": path.stat().st_size,
                "sha256": file_sha256(path),
            })
    entries.sort(key=lambda entry: entry["path"])
    return entries


def inventory_sha256(entries: list[dict[str, Any]]) -> str:
    return hashlib.sha256(canonical_bytes(entries)).hexdigest()


def _run_version(executable: Path) -> tuple[int, str]:
    result = subprocess.run(
        [str(executable), "--version"], capture_output=True, text=True,
        encoding="utf-8", errors="strict", check=False, timeout=30,
    )
    return result.returncode, (result.stdout + result.stderr).strip()


def _is_pe_executable(path: Path) -> bool:
    with path.open("rb") as stream:
        header = stream.read(64)
        if len(header) < 64 or header[:2] != b"MZ":
            return False
        pe_offset = int.from_bytes(header[0x3C:0x40], "little")
        stream.seek(pe_offset)
        return stream.read(4) == b"PE\0\0"


def verify_bundle(
    *,
    root: Path,
    expected_root: Path,
    expected_entries: list[dict[str, Any]],
    expected_inventory_sha256: str,
    expected_file_count: int,
    expected_total_size: int,
    expected_version: str,
    version_runner: Callable[[Path], tuple[int, str]] = _run_version,
    required_key_files: dict[str, tuple[int, str]] = KEY_FILE_IDENTITIES,
    pe_check: Callable[[Path], bool] = _is_pe_executable,
) -> dict[str, Any]:
    resolved_root = Path(root).resolve(strict=True)
    if resolved_root != Path(expected_root).resolve(strict=True):
        raise ValueError("runtime bundle root differs from pinned absolute root")
    actual_entries = inventory(resolved_root)
    if actual_entries != expected_entries:
        raise ValueError("runtime bundle exact file inventory differs from frozen manifest")
    if len(actual_entries) != expected_file_count:
        raise ValueError("runtime bundle file count mismatch")
    total_size = sum(item["size"] for item in actual_entries)
    if total_size != expected_total_size:
        raise ValueError("runtime bundle total byte size mismatch")
    digest = inventory_sha256(actual_entries)
    if digest != expected_inventory_sha256:
        raise ValueError("runtime bundle aggregate inventory hash mismatch")
    by_path = {item["path"]: item for item in actual_entries}
    for relative, (size, sha) in required_key_files.items():
        item = by_path.get(relative)
        if item is None or item["size"] != size or item["sha256"] != sha:
            raise ValueError(f"runtime bundle helper identity mismatch: {relative}")
    executable = resolved_root / "bin" / "codex.exe"
    sibling_host = executable.parent / "codex-code-mode-host.exe"
    if sibling_host != resolved_root / "bin" / "codex-code-mode-host.exe" or not sibling_host.is_file():
        raise ValueError("required Code Mode host is not the exact codex.exe sibling")
    executable_helpers = [
        executable,
        sibling_host,
        resolved_root / "codex-resources" / "codex-command-runner.exe",
        resolved_root / "codex-resources" / "codex-windows-sandbox-setup.exe",
        resolved_root / "codex-path" / "rg.exe",
    ]
    if any(not pe_check(path) for path in executable_helpers):
        raise ValueError("a pinned runtime executable/helper is not a readable Windows PE")
    code, observed = version_runner(executable)
    if code != 0 or observed != expected_version:
        raise ValueError("bundled codex.exe --version does not match pinned runtime version")
    # Recheck key bytes after the version process to reduce check/use drift.
    for relative, (size, sha) in required_key_files.items():
        path = resolved_root / Path(relative)
        if not path.is_file() or path.stat().st_size != size or file_sha256(path) != sha:
            raise ValueError(f"runtime bundle file changed during verification: {relative}")
    # Include every file in the post-execution check, not only the named helpers.
    # This detects additions, removals, or mutations while --version was running.
    if inventory(resolved_root) != expected_entries:
        raise ValueError("runtime bundle changed during version verification")
    return {
        "bundle_root_absolute_path": str(resolved_root),
        "bundle_manifest_schema_version": "codex_vendor_runtime_bundle_inventory.v1",
        "file_count": len(actual_entries),
        "total_byte_size": total_size,
        "canonical_inventory_sha256": digest,
        "executable_relative_path": "bin/codex.exe",
        "executable_absolute_path": str(executable),
        "executable_observed_version": observed,
        "executable_sha256": by_path["bin/codex.exe"]["sha256"],
        "code_mode_host_relative_path": "bin/codex-code-mode-host.exe",
        "code_mode_host_sha256": by_path["bin/codex-code-mode-host.exe"]["sha256"],
        "command_runner_relative_path": "codex-resources/codex-command-runner.exe",
        "command_runner_sha256": by_path["codex-resources/codex-command-runner.exe"]["sha256"],
        "sandbox_setup_relative_path": "codex-resources/codex-windows-sandbox-setup.exe",
        "sandbox_setup_sha256": by_path["codex-resources/codex-windows-sandbox-setup.exe"]["sha256"],
        "package_descriptor_relative_path": "codex-package.json",
        "package_descriptor_sha256": by_path["codex-package.json"]["sha256"],
        "rg_relative_path": "codex-path/rg.exe",
        "rg_sha256": by_path["codex-path/rg.exe"]["sha256"],
    }


def verify_source_target_equivalence(source: Path, target: Path) -> dict[str, Any]:
    source_entries = inventory(source)
    target_entries = inventory(target)
    if source_entries != target_entries:
        raise ValueError("source and copied Codex runtime bundle manifests differ")
    result = {
        "file_count": len(source_entries),
        "total_byte_size": sum(item["size"] for item in source_entries),
        "inventory_sha256": inventory_sha256(source_entries),
        "source_entries": source_entries,
        "target_entries": target_entries,
    }
    if result["file_count"] != EXPECTED_FILE_COUNT or result["total_byte_size"] != EXPECTED_TOTAL_SIZE:
        raise ValueError("source/target runtime bundle size or count differs from accepted authority")
    if result["inventory_sha256"] != EXPECTED_BUNDLE_INVENTORY_SHA256:
        raise ValueError("source/target runtime bundle inventory differs from accepted authority")
    return result


def build_verified_bundle_identity() -> tuple[dict[str, Any], dict[str, Any]]:
    """Measure vendor source plus complete target; never trust caller identity facts."""
    source_entries = inventory(SOURCE_ROOT)
    source_hash = inventory_sha256(source_entries)
    if len(source_entries) != EXPECTED_FILE_COUNT or sum(item["size"] for item in source_entries) != EXPECTED_TOTAL_SIZE:
        raise ValueError("installed vendor source bundle count/size differs from the frozen authority")
    if source_hash != EXPECTED_BUNDLE_INVENTORY_SHA256:
        raise ValueError("installed vendor source bundle hash differs from the frozen authority")
    copied = verify_source_target_equivalence(SOURCE_ROOT, BUNDLE_ROOT)
    identity = verify_bundle(
        root=BUNDLE_ROOT, expected_root=BUNDLE_ROOT, expected_entries=source_entries,
        expected_inventory_sha256=EXPECTED_BUNDLE_INVENTORY_SHA256,
        expected_file_count=EXPECTED_FILE_COUNT, expected_total_size=EXPECTED_TOTAL_SIZE,
        expected_version=EXPECTED_VERSION,
    )
    return identity, copied


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


def _launch_contract_from_identity(bundle_identity: dict[str, Any]) -> dict[str, Any]:
    # Internal constructor. The public builder below derives this object only
    # from a full source/target measurement.
    if bundle_identity.get("bundle_root_absolute_path") != str(BUNDLE_ROOT):
        raise ValueError("wrong pinned bundle root")
    if bundle_identity.get("canonical_inventory_sha256") != EXPECTED_BUNDLE_INVENTORY_SHA256:
        raise ValueError("wrong pinned bundle inventory")
    if bundle_identity.get("executable_observed_version") != EXPECTED_VERSION:
        raise ValueError("wrong pinned executable version")
    server = {
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
        "schema_version": "phase_j_real_agent_attempt_5_launch_contract.v1",
        "codex_runtime_bundle_identity": bundle_identity,
        "formal_executable_absolute_path": str(BUNDLE_ROOT / "bin" / "codex.exe"),
        "formal_cli_grammar": ["exec", "--ignore-user-config", "--ephemeral", "--json", "--output-last-message", "--cd", "-c", "-"],
        "repository_cwd": str(ROOT),
        "mcp_server_name": "phase_j_witness",
        "mcp_server_template": server,
        "control_package_id": CONTROL_ID,
        "package_inventory_sha256": PACKAGE_INVENTORY_SHA256,
        "result_id": RESULT_ID,
        "result_sha256": RESULT_SHA256,
        "audit_id": AUDIT_ID,
        "audit_sha256": AUDIT_SHA256,
        "handoff_sha256": HANDOFF_SHA256,
        "local_service_url": SERVICE_URL,
        "prompt_path": str(PROMPT_PATH),
        "prompt_sha256": PROMPT_SHA256,
        "maximum_slots": MAXIMUM_SLOTS,
        "attempt_evidence_root": str(ATTEMPT_ROOT),
        "slot_path_template": "attempt5-slot-{slot:02d}/{witness-events.jsonl,codex-events.jsonl,codex-stderr.txt,agent-final.txt,slot-receipt.json}",
        "stdout_capture": "Codex JSONL stdout -> slot codex-events.jsonl",
        "stderr_capture": "Codex stderr -> slot codex-stderr.txt",
        "final_output_capture": "--output-last-message -> slot agent-final.txt",
        "witness_capture": "phase_j_witness proxy --log -> slot witness-events.jsonl",
        "semantic_call_policy": {"maximum_calls": 2, "ordered_tools": SEMANTIC_TOOLS, "exact_arguments": {"control_package_id": CONTROL_ID}},
        "expected_tools": TOOLS,
        "attempt4_terminal": True,
        "attempt4_unused_slots_not_transferable": True,
        "attempt5_slots_reserved": 0,
        "attempt5_slots_launched": 0,
    }


def build_launch_contract() -> dict[str, Any]:
    identity, _ = build_verified_bundle_identity()
    return _launch_contract_from_identity(identity)


def validate_launch_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != "phase_j_real_agent_attempt_5_launch_contract.v1":
        raise ValueError("Attempt #5 launch-contract schema mismatch")
    if contract.get("formal_executable_absolute_path") != str(BUNDLE_ROOT / "bin" / "codex.exe"):
        raise ValueError("formal executable is not the exact bundled codex.exe")
    if contract.get("mcp_server_name") != "phase_j_witness":
        raise ValueError("wrong formal MCP server name")
    if contract.get("repository_cwd") != str(ROOT) or contract.get("control_package_id") != CONTROL_ID:
        raise ValueError("repository or retained package binding mismatch")
    if contract.get("maximum_slots") != MAXIMUM_SLOTS or contract.get("attempt5_slots_reserved") != 0 or contract.get("attempt5_slots_launched") != 0:
        raise ValueError("Attempt #5 must retain three unused slots and reserve none in R0")
    if contract.get("attempt4_terminal") is not True or contract.get("attempt4_unused_slots_not_transferable") is not True:
        raise ValueError("Attempt #4 terminal state must not transfer unused slots")
    server = contract.get("mcp_server_template", {})
    if server.get("enabled") is not True or server.get("required") is not True or server.get("startup_timeout_sec") != 30:
        raise ValueError("witness server must be enabled, required, and use the reviewed startup timeout")
    if server.get("command") != str(PYTHON) or server.get("cwd") != str(ROOT):
        raise ValueError("witness proxy Python or working directory mismatch")
    expected_args = [str(PROXY), "--log", "<SLOT>/witness-events.jsonl", "--control-package-id", CONTROL_ID]
    if server.get("args") != expected_args:
        raise ValueError("witness proxy path or arguments mismatch")
    if server.get("env", {}).get("UNIFIED_MARKET_EVIDENCE_SERVICE_URL") != SERVICE_URL:
        raise ValueError("Local Service URL mismatch")
    if contract.get("prompt_sha256") != PROMPT_SHA256 or file_sha256(Path(contract.get("prompt_path", ""))) != PROMPT_SHA256:
        raise ValueError("neutral prompt hash mismatch")
    if contract.get("package_inventory_sha256") != PACKAGE_INVENTORY_SHA256:
        raise ValueError("retained product package inventory mismatch")
    if contract.get("expected_tools") != TOOLS:
        raise ValueError("MCP six-tool inventory mismatch")
    if contract.get("formal_cli_grammar") != ["exec", "--ignore-user-config", "--ephemeral", "--json", "--output-last-message", "--cd", "-c", "-"]:
        raise ValueError("formal Codex command grammar differs from the reviewed contract")
    if contract.get("attempt_evidence_root") != str(ATTEMPT_ROOT):
        raise ValueError("Attempt #5 evidence root mismatch")
    if contract.get("stdout_capture") != "Codex JSONL stdout -> slot codex-events.jsonl" or contract.get("stderr_capture") != "Codex stderr -> slot codex-stderr.txt" or contract.get("witness_capture") != "phase_j_witness proxy --log -> slot witness-events.jsonl":
        raise ValueError("formal evidence stream capture contract mismatch")
    if contract.get("semantic_call_policy") != {"maximum_calls": 2, "ordered_tools": SEMANTIC_TOOLS, "exact_arguments": {"control_package_id": CONTROL_ID}}:
        raise ValueError("semantic MCP call policy mismatch")
    identity = contract.get("codex_runtime_bundle_identity", {})
    if identity.get("bundle_root_absolute_path") != str(BUNDLE_ROOT) or identity.get("canonical_inventory_sha256") != EXPECTED_BUNDLE_INVENTORY_SHA256:
        raise ValueError("full Codex runtime bundle authority mismatch")
    if identity.get("file_count") != EXPECTED_FILE_COUNT or identity.get("total_byte_size") != EXPECTED_TOTAL_SIZE:
        raise ValueError("full Codex runtime bundle count or byte size mismatch")
    if identity.get("executable_observed_version") != EXPECTED_VERSION:
        raise ValueError("full Codex runtime executable version mismatch")
    for key, (size, sha) in KEY_FILE_IDENTITIES.items():
        if key == "bin/codex.exe":
            if identity.get("executable_sha256") != sha:
                raise ValueError("bundled Codex executable hash mismatch")
        elif key == "bin/codex-code-mode-host.exe":
            if identity.get("code_mode_host_sha256") != sha:
                raise ValueError("Code Mode host hash mismatch")
        elif key == "codex-resources/codex-command-runner.exe":
            if identity.get("command_runner_sha256") != sha:
                raise ValueError("command runner hash mismatch")
        elif key == "codex-resources/codex-windows-sandbox-setup.exe":
            if identity.get("sandbox_setup_sha256") != sha:
                raise ValueError("sandbox helper hash mismatch")
        elif key == "codex-package.json":
            if identity.get("package_descriptor_sha256") != sha:
                raise ValueError("package descriptor hash mismatch")
        elif key == "codex-path/rg.exe" and identity.get("rg_sha256") != sha:
            raise ValueError("rg helper hash mismatch")
    if identity.get("executable_relative_path") != "bin/codex.exe" or identity.get("code_mode_host_relative_path") != "bin/codex-code-mode-host.exe":
        raise ValueError("runtime helper paths are not the bundled layout")
    expected_relative_paths = {
        "command_runner_relative_path": "codex-resources/codex-command-runner.exe",
        "sandbox_setup_relative_path": "codex-resources/codex-windows-sandbox-setup.exe",
        "package_descriptor_relative_path": "codex-package.json",
        "rg_relative_path": "codex-path/rg.exe",
    }
    for field, expected_path in expected_relative_paths.items():
        if identity.get(field) != expected_path:
            raise ValueError(f"runtime helper relative path mismatch: {field}")
    if identity.get("executable_absolute_path") != str(BUNDLE_ROOT / "bin" / "codex.exe"):
        raise ValueError("runtime executable path is not derived from the pinned bundle")


def verify_contract_runtime_identity(contract: dict[str, Any], expected_contract_sha256: str) -> dict[str, Any]:
    """Full pre-reservation gate: frozen contract plus fresh measured bundle identity."""
    validate_launch_contract(contract)
    if canonical_sha256(contract) != expected_contract_sha256:
        raise ValueError("launch contract hash differs from reviewed authority")
    actual_identity, _ = build_verified_bundle_identity()
    if actual_identity != contract.get("codex_runtime_bundle_identity"):
        raise ValueError("measured complete runtime bundle differs from reviewed contract")
    return actual_identity


def slot_paths(slot: int, *, root: Path | None = None) -> dict[str, str]:
    if isinstance(slot, bool) or not isinstance(slot, int) or not 1 <= slot <= MAXIMUM_SLOTS:
        raise ValueError("slot number must be between 1 and 3")
    directory = (ATTEMPT_ROOT if root is None else Path(root)) / f"attempt5-slot-{slot:02d}"
    return {
        "directory": str(directory),
        "witness_events": str(directory / "witness-events.jsonl"),
        "codex_events": str(directory / "codex-events.jsonl"),
        "codex_stderr": str(directory / "codex-stderr.txt"),
        "agent_final": str(directory / "agent-final.txt"),
        "slot_receipt": str(directory / "slot-receipt.json"),
        "reservation": str(directory / "slot-reserved.json"),
    }


def derive_slot_contract(contract: dict[str, Any], slot: int, *, root: Path | None = None) -> dict[str, Any]:
    validate_launch_contract(contract)
    paths = slot_paths(slot, root=root)
    if any(Path(value).exists() for key, value in paths.items() if key != "directory") or Path(paths["directory"]).exists():
        raise ValueError("Attempt #5 slot evidence path is not fresh")
    server = dict(contract["mcp_server_template"])
    server["args"] = [str(PROXY), "--log", paths["witness_events"], "--control-package-id", CONTROL_ID]
    server["env"] = {
        "PHASEJ_WITNESS_PROXY_LOG": paths["witness_events"],
        "UNIFIED_MARKET_EVIDENCE_SERVICE_URL": SERVICE_URL,
    }
    override = "mcp_servers.phase_j_witness=" + _toml(server)
    command = [
        contract["formal_executable_absolute_path"], "exec", "--ignore-user-config", "--ephemeral", "--json",
        "--output-last-message", paths["agent_final"], "--cd", str(ROOT), "-c", override, "-",
    ]
    return {"slot": slot, "paths": paths, "mcp_server": {"name": "phase_j_witness", **server},
            "configuration_override": override, "formal_command": command,
            "stdout_path": paths["codex_events"], "stderr_path": paths["codex_stderr"]}
