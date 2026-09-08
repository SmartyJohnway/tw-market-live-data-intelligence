#!/usr/bin/env python3
"""Offline verification for the tested Python dependency contract."""

from __future__ import annotations

import importlib
import importlib.metadata
import json
import platform
import sys

SUPPORTED = {(3, 11), (3, 13)}
REQUIRED = {
    "mcp": "1.29.0",
    "jsonschema": None,
    "requests": None,
    "httpx": None,
    "fastapi": None,
    "uvicorn": None,
    "pandas": None,
}


def main() -> int:
    failures: list[dict[str, str]] = []
    version = sys.version_info[:2]
    if version not in SUPPORTED:
        failures.append(
            {
                "reason_code": "unsupported_python_version",
                "actual": platform.python_version(),
            }
        )
    versions: dict[str, str] = {}
    for package, expected in REQUIRED.items():
        try:
            importlib.import_module(package)
            actual = importlib.metadata.version(package)
            versions[package] = actual
            if expected is not None and actual != expected:
                failures.append(
                    {
                        "reason_code": "package_version_mismatch",
                        "package": package,
                        "expected": expected,
                        "actual": actual,
                    }
                )
        except Exception as exc:
            failures.append(
                {
                    "reason_code": "critical_import_failed",
                    "package": package,
                    "detail": type(exc).__name__,
                }
            )
    report = {
        "status": "PASS" if not failures else "FAIL",
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": versions,
        "failures": failures,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
