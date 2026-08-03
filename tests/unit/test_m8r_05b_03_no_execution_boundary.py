from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "scripts" / "m8r_05b_03"


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
    forbidden_import_roots = {"requests", "httpx", "urllib", "socket", "sqlite3", "subprocess", "queue"}
    for path in PACKAGE.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported = {alias.name.split(".")[0] for alias in node.names}
                assert not imported & forbidden_import_roots
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in forbidden_import_roots


def test_preflight_does_not_mutate_output_root(tmp_path):
    from tests.unit.m8r_05b_03_test_helpers import build_valid_preflight

    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    build_valid_preflight(tmp_path)
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert after == before == []
