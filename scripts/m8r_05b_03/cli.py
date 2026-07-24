"""Preflight-only local CLI for M8R-05B-03 Commit 1."""
from __future__ import annotations

import argparse
import json
import sys

from .artifact_loader import load_json_object
from .errors import OrchestrationError
from .preflight import build_orchestrator_preflight


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-input", required=True)
    parser.add_argument("--authorization-input", required=True)
    parser.add_argument("--consumption-binding-input", required=True)
    parser.add_argument("--consumption-state-input", required=True)
    parser.add_argument("--executor-registry-metadata-input", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--evaluation-timestamp", required=True)
    args = parser.parse_args(argv)
    try:
        artifact = build_orchestrator_preflight(
            load_json_object(args.plan_input),
            load_json_object(args.authorization_input),
            load_json_object(args.consumption_binding_input),
            supplied_consumption_state=load_json_object(args.consumption_state_input),
            evaluation_timestamp=args.evaluation_timestamp,
            executor_registry_metadata=load_json_object(args.executor_registry_metadata_input),
            output_root=args.output_root,
        )
    except OrchestrationError as exc:
        print(json.dumps({"error_code": exc.code}, sort_keys=True), file=sys.stderr)
        return 2
    except OSError:
        print(json.dumps({"error_code": "artifact_load_failed"}, sort_keys=True), file=sys.stderr)
        return 3
    print(json.dumps(artifact, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
