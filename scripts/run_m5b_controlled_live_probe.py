"""M5B controlled live-probe runner interface preflight.

This script intentionally does not execute market-data network calls yet. It defines the
future M5B runner contract, including explicit output-directory handling, so M5A
requests can validate that a proposed runner is capable of honoring the authorized
output path before any separate live-probe authorization is granted.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_OUTPUT_ROOT = Path("research/live_probe_runs/m5b")
ALLOWED_SOURCES = ("TWSE_OpenAPI", "TPEx_OpenAPI", "TWSE_MIS", "Yahoo_Finance")
MAX_TARGETS = 5


def _safe_under_output_root(path_text: str) -> bool:
    path = Path(path_text)
    return not path.is_absolute() and ".." not in path.parts and (path == ALLOWED_OUTPUT_ROOT or ALLOWED_OUTPUT_ROOT in path.parents)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="M5B controlled live-probe interface preflight only; no network execution.")
    parser.add_argument("--source", required=True, choices=ALLOWED_SOURCES, help="Single source for future bounded M5B execution")
    parser.add_argument("--targets", required=True, nargs="+", help="One to five bounded targets")
    parser.add_argument("--output-dir", required=True, help="Authorized output directory under research/live_probe_runs/m5b/")
    parser.add_argument("--check-only", action="store_true", help="Validate runner interface without network or writes")
    return parser


def validate_args(args: argparse.Namespace) -> list[dict]:
    errors = []
    if not args.targets:
        errors.append({"code": "targets_empty", "path": "$.targets"})
    if len(args.targets) > MAX_TARGETS:
        errors.append({"code": "too_many_targets", "path": "$.targets"})
    if len(args.targets) != len(set(args.targets)):
        errors.append({"code": "duplicate_targets", "path": "$.targets"})
    if not _safe_under_output_root(args.output_dir):
        errors.append({"code": "output_path_not_m5b", "path": "$.output_dir"})
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    errors = validate_args(args)
    result = {
        "ok": not errors,
        "errors": errors,
        "runner_interface": "m5b_controlled_live_probe.preflight.v1",
        "check_only": bool(args.check_only),
        "network_used": False,
        "writes": False,
        "execution_performed": False,
        "live_probe_authorized": False,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
