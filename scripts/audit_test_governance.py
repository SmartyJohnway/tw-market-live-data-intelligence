#!/usr/bin/env python3
"""Deterministic TG-0 inventory for test-governance classification.

This tool is intentionally read-only with respect to repository authority.
It scans the explicit default-ci path set and emits classification signals.
It does not change test selection and does not decide that a test is safe to
remove from default CI.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PROFILE_PATH = ROOT / "config" / "test_execution_profiles.json"

HISTORICAL_NAME_RE = re.compile(
    r"(?:final_acceptance|consolidated_acceptance|closure|preflight|"
    r"milestone|promotion|readiness)",
    re.IGNORECASE,
)
CURRENT_SECURITY_RE = re.compile(
    r"(?:security|filesystem|containment|forbidden|authorization|execute_once|"
    r"mode_b2|identity|watchlist)",
    re.IGNORECASE,
)
DOC_PATH_RE = re.compile(r"(?:^|[\"'])(docs/[^\"']+)")
MARKDOWN_LITERAL_RE = re.compile(r"(?:README(?:\.zh-TW)?\.md|\.md(?:\b|$))", re.IGNORECASE)
NEXT_TASK_RE = re.compile(r"next_task", re.IGNORECASE)
LEDGER_RE = re.compile(r"(?:ledger|manifest|acceptance|protocol)", re.IGNORECASE)

CLASS_ORDER = (
    "CURRENT_CORE",
    "CURRENT_CONTRACT",
    "COMPATIBILITY",
    "CURRENT_INTEGRATION",
    "RELEASE_PRECHECK",
    "HISTORICAL_ACCEPTANCE",
    "DOCUMENTATION_GOVERNANCE",
    "REVIEW_REQUIRED",
)


def _load_profile_paths(profile_name: str = "default-ci") -> list[str]:
    payload = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    return list(payload["profiles"][profile_name]["pytest_paths"])


def _decorator_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parts: list[str] = []
        current: ast.expr = node
        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name):
            parts.append(current.id)
            return ".".join(reversed(parts))
    if isinstance(node, ast.Call):
        return _decorator_name(node.func)
    return None


def _test_nodes(tree: ast.AST) -> list[ast.AST]:
    out: list[ast.AST] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            out.append(node)
    return out


def _string_literals(tree: ast.AST) -> list[str]:
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            out.append(node.value)
    return out


def _assert_string_signals(tree: ast.AST) -> tuple[int, int]:
    """Return (exact_path_assertions, prose_assertions) heuristic counts."""
    path_count = 0
    prose_count = 0
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert):
            continue
        literals = [
            child.value
            for child in ast.walk(node.test)
            if isinstance(child, ast.Constant) and isinstance(child.value, str)
        ]
        for value in literals:
            stripped = value.strip()
            if "/" in stripped or MARKDOWN_LITERAL_RE.search(stripped):
                path_count += 1
            if (
                len(stripped) >= 32
                and "://" not in stripped
                and not re.fullmatch(r"[A-Za-z0-9_.:/# -]+", stripped)
            ):
                prose_count += 1
            elif len(stripped.split()) >= 7 and not stripped.startswith(("http://", "https://")):
                prose_count += 1
    return path_count, prose_count


def _imports(tree: ast.AST) -> list[str]:
    items: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            items.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            items.append(node.module)
    return sorted(set(items))


def _family(path: str) -> str:
    name = Path(path).name
    if name.startswith("test_phase_h"):
        return "phase_h"
    if name.startswith("test_phase_g"):
        return "phase_g"
    match = re.match(r"test_(m\d+r?|m8r)[^_]*", name, flags=re.IGNORECASE)
    if match:
        return match.group(1).lower()
    if "m8r_" in name:
        return "m8r"
    if "m8" in name:
        return "m8"
    if "m7" in name:
        return "m7"
    if "m6" in name:
        return "m6"
    if "m5" in name:
        return "m5"
    return "cross_cutting"


def _suggest_class(
    path: str,
    *,
    markers: set[str],
    reads_docs: bool,
    reads_readme: bool,
    exact_path_assertions: int,
    exact_prose_assertions: int,
    next_task_literals: int,
    imports: list[str],
) -> tuple[str, str]:
    name = Path(path).name.lower()
    production_import = any(
        item == "server"
        or item.startswith("server.")
        or item == "scripts"
        or item.startswith("scripts.")
        for item in imports
    )
    if "historical" in markers or path.startswith("tests/acceptance_archive/"):
        return "HISTORICAL_ACCEPTANCE", "high"
    if "release" in name or "product_version" in name:
        return "RELEASE_PRECHECK", "medium"
    if (
        reads_docs
        and (exact_path_assertions or exact_prose_assertions or next_task_literals)
        and HISTORICAL_NAME_RE.search(name)
    ):
        return "HISTORICAL_ACCEPTANCE", "medium"
    if reads_readme or (
        reads_docs and (exact_path_assertions or exact_prose_assertions)
    ):
        return "DOCUMENTATION_GOVERNANCE", "medium"
    if CURRENT_SECURITY_RE.search(name):
        return "CURRENT_CORE", "medium"
    if "schema" in name or "contract" in name or "catalog" in name or "routing" in name:
        return "CURRENT_CONTRACT", "medium"
    if "integration" in path or "e2e" in name:
        return "CURRENT_INTEGRATION", "medium"
    if production_import and not HISTORICAL_NAME_RE.search(name):
        return "CURRENT_CORE", "low"
    if HISTORICAL_NAME_RE.search(name):
        return "REVIEW_REQUIRED", "low"
    return "REVIEW_REQUIRED", "low"


def analyze(path: str) -> dict[str, Any]:
    file_path = ROOT / path
    if not file_path.is_file():
        return {
            "path": path,
            "exists": False,
            "suggested_class": "REVIEW_REQUIRED",
            "confidence": "high",
            "reason": "profile_path_missing",
        }

    text = file_path.read_text(encoding="utf-8-sig")
    tree = ast.parse(text, filename=path)
    tests = _test_nodes(tree)
    literals = _string_literals(tree)
    imports = _imports(tree)

    markers: set[str] = set()
    for node in tests:
        for decorator in getattr(node, "decorator_list", []):
            name = _decorator_name(decorator)
            if name and name.startswith("pytest.mark."):
                markers.add(name.removeprefix("pytest.mark."))

    file_level_markers: set[str] = set()
    for node in getattr(tree, "body", []):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "pytestmark":
                    for child in ast.walk(node.value):
                        name = _decorator_name(child) if isinstance(child, ast.expr) else None
                        if name and name.startswith("pytest.mark."):
                            file_level_markers.add(name.removeprefix("pytest.mark."))
    markers.update(file_level_markers)

    reads_docs = "docs/" in text
    reads_readme = "README.md" in text or "README.zh-TW.md" in text
    exact_path_assertions, exact_prose_assertions = _assert_string_signals(tree)
    next_task_literals = sum(1 for value in literals if NEXT_TASK_RE.search(value))
    ledger_literals = sum(1 for value in literals if LEDGER_RE.search(value))
    suggested_class, confidence = _suggest_class(
        path,
        markers=markers,
        reads_docs=reads_docs,
        reads_readme=reads_readme,
        exact_path_assertions=exact_path_assertions,
        exact_prose_assertions=exact_prose_assertions,
        next_task_literals=next_task_literals,
        imports=imports,
    )

    return {
        "path": path,
        "exists": True,
        "family": _family(path),
        "test_count": len(tests),
        "markers": sorted(markers),
        "imports_server_or_scripts": [
            item for item in imports
            if item == "server"
            or item.startswith("server.")
            or item == "scripts"
            or item.startswith("scripts.")
        ],
        "reads_docs": reads_docs,
        "reads_readme": reads_readme,
        "exact_path_assertion_signals": exact_path_assertions,
        "exact_prose_assertion_signals": exact_prose_assertions,
        "next_task_literal_signals": next_task_literals,
        "ledger_manifest_protocol_literal_signals": ledger_literals,
        "historical_name_signal": bool(HISTORICAL_NAME_RE.search(Path(path).name)),
        "suggested_class": suggested_class,
        "confidence": confidence,
        "manual_review_required": confidence != "high",
    }


def build_report(profile_name: str = "default-ci") -> dict[str, Any]:
    paths = _load_profile_paths(profile_name)
    records = [analyze(path) for path in paths]

    class_counts = Counter(record["suggested_class"] for record in records)
    family_counts = Counter(record.get("family", "missing") for record in records)
    metrics = {
        "default_ci_file_count": len(paths),
        "existing_file_count": sum(1 for record in records if record.get("exists")),
        "missing_file_count": sum(1 for record in records if not record.get("exists")),
        "static_test_function_count": sum(int(record.get("test_count", 0)) for record in records),
        "files_with_any_marker": sum(1 for record in records if record.get("markers")),
        "files_reading_docs": sum(1 for record in records if record.get("reads_docs")),
        "files_reading_readme": sum(1 for record in records if record.get("reads_readme")),
        "files_with_exact_path_assertion_signal": sum(
            1 for record in records if record.get("exact_path_assertion_signals", 0)
        ),
        "files_with_exact_prose_assertion_signal": sum(
            1 for record in records if record.get("exact_prose_assertion_signals", 0)
        ),
        "files_with_next_task_literal_signal": sum(
            1 for record in records if record.get("next_task_literal_signals", 0)
        ),
        "files_with_historical_name_signal": sum(
            1 for record in records if record.get("historical_name_signal")
        ),
        "manual_review_required": sum(
            1 for record in records if record.get("manual_review_required")
        ),
    }

    return {
        "schema_version": "test_governance_inventory.v1",
        "baseline_profile": profile_name,
        "source_profile_path": "config/test_execution_profiles.json",
        "classification_is_advisory": True,
        "selection_change_performed": False,
        "metrics": metrics,
        "suggested_class_counts": dict(sorted(class_counts.items())),
        "family_counts": dict(sorted(family_counts.items())),
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    report = build_report()
    rendered = json.dumps(
        report,
        indent=2 if args.pretty or args.output else None,
        sort_keys=True,
        ensure_ascii=False,
    )
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
