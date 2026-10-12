"""One-shot MCP call guard for the authorized Phase-J real-agent witness."""
from __future__ import annotations

import hashlib
import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTROL_PACKAGE_ID_PATTERN = re.compile(r"^umea-v1-[0-9a-f]{20}$")
EXPECTED_TOOLS = {
    "market_describe_capabilities", "market_validate_request",
    "market_preview_request", "market_read_result",
    "market_export_ai_handoff", "market_fetch_evidence",
}
ALLOWED_SEQUENCE = ["market_read_result", "market_export_ai_handoff"]
LOG_PATH = Path(os.environ.get(
    "PHASEJ_WITNESS_PROXY_LOG",
    str(Path(tempfile.gettempdir()) / "phasej_real_agent_attempt2_proxy.jsonl"),
))


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def append_event(event: dict[str, object], lock: threading.Lock) -> None:
    with lock:
        with LOG_PATH.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def collect_ids(value: object) -> dict[str, str]:
    found: dict[str, str] = {}
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"result_id", "audit_package_id"} and isinstance(item, str):
                found[key] = item
            found.update(collect_ids(item))
    elif isinstance(value, list):
        for item in value:
            found.update(collect_ids(item))
    return found


def tool_call_is_authorized(
    name: object,
    arguments: object,
    calls: list[str],
    control_package_id: str,
) -> bool:
    expected = ALLOWED_SEQUENCE[len(calls)] if len(calls) < len(ALLOWED_SEQUENCE) else None
    return (
        CONTROL_PACKAGE_ID_PATTERN.fullmatch(control_package_id) is not None
        and name == expected
        and isinstance(arguments, dict)
        and arguments == {"control_package_id": control_package_id}
    )


async def transport_probe() -> int:
    """Exercise initialize/tools/list only; never invoke a semantic tool."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    probe_log = Path(tempfile.gettempdir()) / f"phasej_proxy_probe_{os.getpid()}.jsonl"
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(Path(__file__).resolve()), "--log", str(probe_log)],
    )
    async with stdio_client(params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            initialized = await session.initialize()
            listed = await session.list_tools()
    names = sorted(tool.name for tool in listed.tools)
    exact = len(names) == 6 and set(names) == EXPECTED_TOOLS
    print(json.dumps({
        "initialize": "PASS",
        "protocol_version": initialized.protocolVersion,
        "server_name": initialized.serverInfo.name,
        "server_version": initialized.serverInfo.version,
        "tools_list": "PASS" if exact else "FAIL",
        "tool_count": len(names),
        "tool_names": names,
    }, ensure_ascii=False, sort_keys=True))
    return 0 if exact else 1


def main(control_package_id: str) -> int:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    child = subprocess.Popen(
        [sys.executable, str(ROOT / "scripts" / "run_unified_market_evidence_mcp.py")],
        cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr,
        bufsize=0,
    )
    assert child.stdin is not None and child.stdout is not None
    lock = threading.Lock()
    pending: dict[object, str] = {}
    calls: list[str] = []
    blocked = 0
    tools_ready = threading.Event()
    tools_valid = False

    def client_to_server() -> None:
        nonlocal blocked
        for raw in sys.stdin.buffer:
            try:
                message = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError):
                append_event({"event": "invalid_client_json"}, lock)
                continue
            method = message.get("method")
            request_id = message.get("id")
            if method == "initialize":
                pending[request_id] = "initialize"
                append_event({"event": "initialize_request", "protocolVersion": message.get("params", {}).get("protocolVersion")}, lock)
            if method == "tools/list":
                pending[request_id] = "tools/list"
            if method == "tools/call":
                params = message.get("params") or {}
                name = params.get("name")
                args = params.get("arguments") or {}
                valid = tools_ready.is_set() and tools_valid and tool_call_is_authorized(
                    name, args, calls, control_package_id
                )
                if not valid:
                    blocked += 1
                    append_event({"event": "blocked_tool_call", "name": name, "reason": "tool_order_or_arguments_or_call_limit"}, lock)
                    response = {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Phase-J witness tool policy rejected this call"}}
                    sys.stdout.buffer.write(canonical(response) + b"\n")
                    sys.stdout.buffer.flush()
                    continue
                calls.append(name)
                pending[request_id] = name
                append_event({"event": "tool_call", "ordinal": len(calls), "name": name, "arguments": {"control_package_id": control_package_id}}, lock)
            child.stdin.write(raw)
            child.stdin.flush()
        try:
            child.stdin.close()
        except OSError:
            pass

    def server_to_client() -> None:
        nonlocal tools_valid
        for raw in child.stdout:
            try:
                message = json.loads(raw)
            except (UnicodeDecodeError, json.JSONDecodeError):
                append_event({"event": "invalid_server_json"}, lock)
                sys.stdout.buffer.write(raw)
                sys.stdout.buffer.flush()
                continue
            request_id = message.get("id")
            kind = pending.pop(request_id, None) if request_id is not None else None
            if kind == "tools/list":
                tools = (message.get("result") or {}).get("tools", [])
                names = sorted(tool.get("name", "") for tool in tools)
                tools_valid = set(names) == EXPECTED_TOOLS and len(names) == 6
                tools_ready.set()
                append_event({"event": "tools_list", "count": len(names), "names": names, "exact_six": tools_valid}, lock)
            elif kind == "initialize":
                server_info = (message.get("result") or {}).get("serverInfo") or {}
                append_event({"event": "initialize_result", "protocolVersion": (message.get("result") or {}).get("protocolVersion"), "server_name": server_info.get("name"), "server_version": server_info.get("version")}, lock)
            elif kind in ALLOWED_SEQUENCE:
                result = message.get("result")
                structured = result.get("structuredContent") if isinstance(result, dict) else None
                append_event({
                    "event": "tool_result", "name": kind,
                    "success": isinstance(result, dict) and result.get("isError") is not True and "error" not in message,
                    "result_sha256": hashlib.sha256(canonical(result)).hexdigest(),
                    "bound_ids": collect_ids(structured),
                }, lock)
            sys.stdout.buffer.write(raw)
            sys.stdout.buffer.flush()

    left = threading.Thread(target=client_to_server, daemon=True)
    right = threading.Thread(target=server_to_client, daemon=True)
    left.start()
    right.start()
    left.join()
    right.join()
    try:
        code = child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        child.terminate()
        code = child.wait(timeout=5)
    append_event({"event": "proxy_exit", "adapter_exit_code": code, "tool_call_sequence": calls, "blocked_calls": blocked}, lock)
    return 0 if blocked == 0 else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--log")
    parser.add_argument("--control-package-id")
    options = parser.parse_args()
    if options.log:
        LOG_PATH = Path(options.log)
    if not options.probe and LOG_PATH.exists():
        print("witness proxy log path already exists", file=sys.stderr)
        raise SystemExit(2)
    if options.probe:
        raise SystemExit(asyncio.run(transport_probe()))
    if not options.control_package_id or not CONTROL_PACKAGE_ID_PATTERN.fullmatch(options.control_package_id):
        parser.error("--control-package-id must be an explicit umea-v1-* package identity")
    raise SystemExit(main(options.control_package_id))
