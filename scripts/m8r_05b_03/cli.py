"""Explicit local CLI.  No default output root, no network flag, no scheduler."""
from __future__ import annotations

import argparse
import json
import sys

from .artifact_loader import load_json_object
from .errors import OrchestrationError
from .authorization_gate import approved_operation_map, authorize


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-input", required=True); parser.add_argument("--authorization-input", required=True)
    parser.add_argument("--consumption-binding-input", required=True); parser.add_argument("--consumption-state-input", required=True)
    parser.add_argument("--execution-timestamp", required=True); parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        if not args.check_only:
            raise OrchestrationError("executor_registry_required")
        plan = load_json_object(args.plan_input); authorization = load_json_object(args.authorization_input)
        binding = load_json_object(args.consumption_binding_input); state = load_json_object(args.consumption_state_input)
        authorize(plan, authorization, binding, evaluation_timestamp=args.execution_timestamp, supplied_consumption_state=state)
        result = {"status": "ready_for_injected_executor_registry", "approved_operation_ids": sorted(approved_operation_map(plan, authorization))}
    except OrchestrationError as exc:
        print(json.dumps({"error_code": exc.code}, sort_keys=True), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
