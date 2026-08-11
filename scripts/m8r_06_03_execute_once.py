"""Fixed Mode B2 execute-once child protocol; never a general command runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Running this fixed wrapper by path makes Python place ``scripts/`` rather
# than the repository root on sys.path.  Establish the known server-owned root
# before importing the package contracts; no caller-supplied import path exists.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.m8r_05b_02.consumption_binding import validate_consumption_binding
from scripts.m8r_05b_02.validator import validate_execution_authorization
from scripts.m8r_05b_03.errors import OrchestrationError
from scripts.m8r_05b_03.orchestrator import execute_controlled_plan
from scripts.m8r_05b_03.preflight import validate_preflight_hashes
from scripts.m8r_06_03_production_adapter import (
    build_production_runtime_adapter_registry,
    load_production_executor_metadata,
)
from scripts.m8r_filesystem_safety import safe_destination


# Test harnesses may redirect the server-owned root through process environment;
# no browser/API request can affect this value.
CONTROL_ROOT = Path(os.environ.get("M8R_06_03_CONTROL_ROOT", str(ROOT / "artifacts" / "m8r_06_03_workbench"))).resolve()
ARTIFACTS = (
    "request", "plan", "authorization", "consumption_binding",
    "unused_consumption_state", "preflight",
)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_json(path: Path, code: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise OrchestrationError(code) from exc
    if not isinstance(value, dict):
        raise OrchestrationError(code)
    return value


def load_control_package(authorization_id: str) -> tuple[Path, dict[str, dict[str, Any]], dict[str, Any]]:
    if not isinstance(authorization_id, str) or not authorization_id.startswith("umea-v1-"):
        raise OrchestrationError("control_package_id_invalid")
    package_root = CONTROL_ROOT / authorization_id
    manifest_path = safe_destination(CONTROL_ROOT, f"{authorization_id}/control/manifest.json", create_parent=False).path
    manifest = _load_json(manifest_path, "control_package_manifest_invalid")
    artifacts: dict[str, dict[str, Any]] = {}
    hashes = manifest.get("artifact_hashes")
    if not isinstance(hashes, dict) or set(hashes) != set(ARTIFACTS):
        raise OrchestrationError("control_package_manifest_invalid")
    for name in ARTIFACTS:
        path = safe_destination(CONTROL_ROOT, f"{authorization_id}/control/{name}.json", create_parent=False).path
        content = path.read_bytes()
        if hashlib.sha256(content).hexdigest() != hashes.get(name):
            raise OrchestrationError("control_package_artifact_hash_mismatch")
        try:
            value = json.loads(content)
        except json.JSONDecodeError as exc:
            raise OrchestrationError("control_package_artifact_invalid") from exc
        if not isinstance(value, dict):
            raise OrchestrationError("control_package_artifact_invalid")
        artifacts[name] = value
    plan, authorization, binding, preflight = (artifacts[key] for key in ("plan", "authorization", "consumption_binding", "preflight"))
    if (
        manifest.get("authorization_id") != authorization.get("authorization_id")
        or manifest.get("authorization_hash") != authorization.get("authorization_hash")
        or manifest.get("plan_id") != plan.get("plan_id")
        or manifest.get("plan_hash") != plan.get("plan_hash")
        or manifest.get("preflight_id") != preflight.get("preflight_id")
        or manifest.get("preflight_hash") != preflight.get("preflight_hash")
    ):
        raise OrchestrationError("control_package_binding_mismatch")
    validate_execution_authorization(authorization, plan)
    validate_consumption_binding(binding, authorization, plan)
    validate_preflight_hashes(preflight)
    if preflight.get("authorization_id") != authorization_id:
        raise OrchestrationError("control_package_binding_mismatch")
    claim_path = safe_destination(CONTROL_ROOT, f"{authorization_id}/claims/{authorization_id}.consumption-record.json", create_parent=False).path
    if claim_path.exists():
        raise OrchestrationError("authorization_already_claimed")
    return package_root, artifacts, manifest


def _install_deterministic_test_transport() -> None:
    """A process-local test seam, unavailable to browser request data."""
    if os.environ.get("M8R_06_03_TEST_SOURCE_TRANSPORT") != "deterministic":
        return
    import scripts.m8r_06_03_production_adapter as adapter

    delay_seconds = float(os.environ.get("M8R_06_03_TEST_SOURCE_DELAY_SECONDS", "0"))
    counter_dir = os.environ.get("M8R_06_03_TEST_INVOCATION_COUNTER")

    def record_invocation() -> None:
        if not counter_dir:
            return
        destination = Path(counter_dir)
        destination.mkdir(parents=True, exist_ok=True)
        # Each actual source invocation has one immutable marker.  The parent
        # test counts these markers; browser data cannot enable this seam.
        (destination / f"source-{os.getpid()}-{time.time_ns()}.invoked").write_text("1\n", encoding="ascii")

    def observation(watchlist, **_kwargs):
        record_invocation()
        if delay_seconds:
            time.sleep(delay_seconds)
        return {"observations": [{"symbol": item["symbol"], "source": "deterministic"} for item in watchlist["items"]]}

    def eod(symbols, *, timeout):
        record_invocation()
        if delay_seconds:
            time.sleep(delay_seconds)
        return {"source_id": "deterministic_eod", "observations": [{"symbol": item, "timeout": timeout} for item in symbols]}

    adapter.execute_live_observation = observation
    adapter.execute_twse_official_eod_adapter = eod
    adapter.execute_tpex_official_eod_adapter = eod


def execute_once(authorization_id: str, *, confirm_execution: bool, operator_confirmation_reference: str, confirm_network_execution: bool) -> dict[str, Any]:
    package_root, artifacts, _manifest = load_control_package(authorization_id)
    if confirm_execution is not True:
        raise OrchestrationError("execution_confirmation_required")
    _install_deterministic_test_transport()
    now = _now()
    result = execute_controlled_plan(
        artifacts["plan"], artifacts["authorization"], artifacts["consumption_binding"],
        supplied_consumption_state=artifacts["unused_consumption_state"],
        accepted_preflight=artifacts["preflight"], evaluation_timestamp=now,
        claim_created_at=now, finalized_at=now,
        executor_registry_metadata=load_production_executor_metadata(),
        runtime_adapter_registry=build_production_runtime_adapter_registry(),
        output_root=str(package_root), mode="execute-approved",
        confirm_execution=True, operator_confirmation_reference=operator_confirmation_reference,
        confirm_network_execution=confirm_network_execution,
    )
    return {
        "schema_version": "m8r_06_03_execute_once_result.v1",
        "authorization_id": authorization_id,
        "consumption_state": result["consumption_state"],
        "operation_statuses": [item["status"] for item in result["dispatch_outcomes"]],
        "aggregation_status": result["aggregation"]["overall_status"],
        "execution_receipt_id": result["execution_receipt"]["execution_receipt_id"],
        "evidence_bundle_id": result["evidence_bundle"]["bundle_id"],
        "external_market_network_executed": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fixed M8R-06-03 execute-once child")
    parser.add_argument("--authorization-id", required=True)
    parser.add_argument("--confirm-execution", action="store_true")
    parser.add_argument("--operator-confirmation-reference", required=True)
    parser.add_argument("--confirm-network-execution", action="store_true")
    args = parser.parse_args(argv)
    # Test-only process seam for the *parent's* fixed child protocol checks.
    # It is exclusively environment controlled and never accepts API input.
    protocol_mode = os.environ.get("M8R_06_03_TEST_CHILD_PROTOCOL")
    if protocol_mode == "non_json":
        print("not-json")
        return 0
    if protocol_mode == "incomplete_json":
        print('{"schema_version":')
        return 0
    if protocol_mode == "unexpected_shape":
        print(json.dumps({"unexpected": True}, separators=(",", ":")))
        return 0
    if protocol_mode == "unexpected_nonzero":
        print(json.dumps({"unexpected": True}, separators=(",", ":")))
        return 7
    try:
        result = execute_once(
            args.authorization_id, confirm_execution=args.confirm_execution,
            operator_confirmation_reference=args.operator_confirmation_reference,
            confirm_network_execution=args.confirm_network_execution,
        )
    except (OrchestrationError, ValueError, KeyError):
        print(json.dumps({"error": "mode_b2_execution_unavailable"}, separators=(",", ":")))
        return 2
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
