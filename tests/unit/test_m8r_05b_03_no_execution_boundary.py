from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "scripts" / "m8r_05b_03"


def scan_code_for_boundary_violations(source: str, filename: str = "test.py") -> list[str]:
    violations: list[str] = []
    tree = ast.parse(source, filename=filename)

    forbidden_import_roots = {"requests", "httpx", "urllib", "socket", "sqlite3", "subprocess", "queue", "importlib"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in forbidden_import_roots:
                    violations.append(f"forbidden_import:{root}")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                root = node.module.split(".")[0]
                if root in forbidden_import_roots:
                    violations.append(f"forbidden_import:{root}")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == "__import__":
                    violations.append("forbidden_call:__import__")
            elif isinstance(node.func, ast.Attribute):
                if node.func.attr == "import_module":
                    violations.append("forbidden_call:import_module")

    if "while True:" in source or "while 1:" in source:
        violations.append("forbidden_pattern:polling_loop")
    if 'state = "unused"' in source or "state['state'] = 'unused'" in source:
        violations.append("forbidden_pattern:reset_to_unused")

    return violations


def test_public_surface_does_not_export_aggregation_or_receipt():
    source = (PACKAGE / "__init__.py").read_text(encoding="utf-8")
    assert "execute_controlled_plan" not in source
    assert "aggregate_evidence" not in source
    assert "build_execution_receipt" not in source
    assert "build_orchestrator_preflight" in source
    assert "claim_and_dispatch_approved" in source


def test_no_aggregation_or_receipt_modules_exist():
    forbidden = [
        "evidence_aggregation.py",
        "receipt.py",
        "orchestrator.py",
    ]
    assert not any((PACKAGE / name).exists() for name in forbidden)


def test_no_network_database_queue_or_subprocess_imports():
    for path in PACKAGE.glob("*.py"):
        source = path.read_text(encoding="utf-8")
        violations = scan_code_for_boundary_violations(source, path.name)
        assert violations == [], f"Boundary violations in {path.name}: {violations}"


def test_preflight_does_not_mutate_output_root(tmp_path):
    from tests.unit.m8r_05b_03_test_helpers import build_valid_preflight

    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    build_valid_preflight(tmp_path)
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert after == before == []


def test_boundary_scanner_synthetic_positive_and_negative_controls():
    # Negative control 1: __import__
    snippet_bad1 = "mod = __import__('requests')"
    assert "forbidden_call:__import__" in scan_code_for_boundary_violations(snippet_bad1)

    # Negative control 2: importlib
    snippet_bad2 = "import importlib; importlib.import_module('foo')"
    violations2 = scan_code_for_boundary_violations(snippet_bad2)
    assert any("forbidden" in v for v in violations2)

    # Negative control 3: polling loop
    snippet_bad3 = "while True:\n    pass"
    assert "forbidden_pattern:polling_loop" in scan_code_for_boundary_violations(snippet_bad3)

    # Positive control: valid code snippet
    snippet_good = "def foo():\n    return {'status': 'ok'}"
    assert scan_code_for_boundary_violations(snippet_good) == []
