from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.repo_safety_preflight import evaluate_repo_safety, is_forbidden_changed_path
def test_preflight_required_files_ok(): assert evaluate_repo_safety(ROOT, [])['ok']
def test_forbidden_paths_blocked(): assert is_forbidden_changed_path('frontend/public/x.json'); assert is_forbidden_changed_path('research/generated/x.json')
def test_injected_changed_files_fail(): assert not evaluate_repo_safety(ROOT, ['.env'])['ok']
