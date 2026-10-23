"""Thin container process adapter around the canonical Local Service lifecycle."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
PROFILE_ENV = "TW_MARKET_NETWORK_PROFILE"
PROFILE = "docker-local-service"
PORT_ENV = "TW_MARKET_PORT"


def default_ipv4_gateway(route_file: Path = Path("/proc/net/route")) -> str:
    try:
        for row in route_file.read_text(encoding="ascii").splitlines()[1:]:
            fields = row.split()
            if len(fields) < 4 or fields[1] != "00000000" or not (int(fields[3], 16) & 0x2):
                continue
            raw = bytes.fromhex(fields[2])
            if len(raw) == 4:
                return socket.inet_ntoa(raw[::-1])
    except (OSError, ValueError, IndexError):
        pass
    raise RuntimeError("docker_network_gateway_unavailable")


def _lifecycle(command: str) -> tuple[int, dict[str, object]]:
    completed = subprocess.run(
        [sys.executable, "-m", "scripts.tw_market", command, "--json"],
        cwd=ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    try:
        payload = json.loads(completed.stdout)
    except (TypeError, json.JSONDecodeError):
        payload = {"status": "FAIL", "reason_code": "LIFECYCLE_OUTPUT_INVALID"}
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, flush=True)
    print(json.dumps({"command": command, "returncode": completed.returncode, **payload}, sort_keys=True), flush=True)
    return completed.returncode, payload


def serve() -> int:
    if os.environ.get(PROFILE_ENV) != PROFILE:
        print("docker_network_profile_required", file=sys.stderr, flush=True)
        return 2
    try:
        os.environ["TW_MARKET_DOCKER_GATEWAY_IP"] = default_ipv4_gateway()
        from server.local_network_boundary import _default_ipv4_subnet
        os.environ["TW_MARKET_DOCKER_SUBNET"] = _default_ipv4_subnet()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr, flush=True)
        return 2
    code, status = _lifecycle("status")
    installation = status.get("installation") if isinstance(status, dict) else None
    if code != 0 or not isinstance(installation, dict) or installation.get("installation_status") != "READY":
        print("installation_not_initialized; run the explicit Docker init command", file=sys.stderr, flush=True)
        return 1
    code, result = _lifecycle("start")
    if code != 0 or result.get("status") not in {"STARTED", "ALREADY_RUNNING"}:
        return 1

    stopped = threading.Event()

    def request_stop(_signum, _frame):
        stopped.set()

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    while not stopped.wait(1):
        try:
            with urlopen("http://127.0.0.1:8000/api/health", timeout=2) as response:
                healthy = response.status == 200
        except (OSError, URLError):
            healthy = False
        if not healthy:
            print("local_service_unhealthy", file=sys.stderr, flush=True)
            _lifecycle("stop")
            return 1
    stop_code, stop_result = _lifecycle("stop")
    return 0 if stop_code == 0 and stop_result.get("status") in {"STOPPED", "NOT_RUNNING"} else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("serve", "init", "status", "stop", "doctor"))
    args = parser.parse_args(argv)
    if args.command == "serve":
        return serve()
    if args.command == "init":
        return _lifecycle("init")[0]
    if args.command == "status":
        return _lifecycle("status")[0]
    if args.command == "doctor":
        return _lifecycle("doctor")[0]
    return _lifecycle("stop")[0]


if __name__ == "__main__":
    raise SystemExit(main())
