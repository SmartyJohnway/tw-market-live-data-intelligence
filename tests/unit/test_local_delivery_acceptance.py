import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import pytest
from pathlib import Path
from scripts.run_local_delivery_acceptance import run_acceptance_checks, write_acceptance_report

def test_check_only_pass_on_repo(): assert run_acceptance_checks(Path.cwd())["ok"] is True
def test_missing_required_file_returns_failure_object_not_exception(tmp_path):
    r=run_acceptance_checks(tmp_path); assert r["ok"] is False and r["checks"]
def test_forbidden_string_detection(tmp_path):
    (tmp_path/"docs/contracts").mkdir(parents=True); (tmp_path/"docs/contracts/frontend_readonly_context_package_schema.md").write_text("realtime_guaranteed: true")
    r=run_acceptance_checks(tmp_path); assert r["ok"] is False
def test_write_report_to_tmp_path(tmp_path): assert write_acceptance_report({"ok":True}, tmp_path/"r.json").exists()
def test_write_report_to_frontend_public_fails_closed(tmp_path):
    with pytest.raises(ValueError): write_acceptance_report({"ok":True}, tmp_path/"frontend/public/r.json")
def test_write_report_to_research_generated_fails_closed(tmp_path):
    with pytest.raises(ValueError): write_acceptance_report({"ok":True}, tmp_path/"research/generated/r.json")
