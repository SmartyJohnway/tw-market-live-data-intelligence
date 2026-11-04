"""Regression: CPython isolation and non-ASCII Native bootstrap on Windows."""
from __future__ import annotations
import ast
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def test_isolated_utf8_outputs_nonascii_even_when_environment_requests_ascii():
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "ascii"
    code = "import sys,json; print(json.dumps({'mode':sys.flags.utf8_mode,'text':'非ASCII'},ensure_ascii=False))"
    result = subprocess.run(
        [sys.executable, "-I", "-B", "-Xutf8", "-c", code],
        env=env, capture_output=True, text=True, encoding="utf-8", check=True)
    parsed = json.loads(result.stdout)
    assert parsed == {"mode": 1, "text": "非ASCII"}

def test_pip_install_preserves_isolation_hash_lock_and_utf8():
    path = ROOT / "packaging_native" / "bootstrap" / "bootstrap.py"
    root = ast.parse(path.read_text(encoding="utf-8"))
    installs = [node for node in ast.walk(root)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "_checked_child" and node.args
                and isinstance(node.args[0], ast.Constant) and node.args[0].value == "PIP_INSTALL"]
    assert len(installs) == 1
    literals = {node.value for node in ast.walk(installs[0].args[1])
                if isinstance(node, ast.Constant) and isinstance(node.value, str)}
    assert {"-I", "-B", "-Xutf8", "-m", "pip", "--isolated",
            "--no-cache-dir", "--no-index", "--only-binary=:all:",
            "--require-hashes"}.issubset(literals)
def test_acceptance_guard_recognizes_utf8_flag_without_dropping_audit():
    text = (ROOT / "packaging_native" / "acceptance_guard.py").read_text(encoding="utf-8")
    assert "sys.addaudithook(audit)" in text
    assert "'-Xutf8'" in text
    assert "subprocess.Popen=GuardedPopen" in text
