import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))

from scripts.run_ci_delivery_acceptance import run_ci_delivery_acceptance, main
def test_ci_wrapper_check_only():
    r=run_ci_delivery_acceptance(ROOT); assert r['ok'] and r['check_only'] and r['network'] is False
def test_write_report_tmp_path(tmp_path):
    out=tmp_path/'report.json'; assert main(['--repo-root',str(ROOT),'--write-report',str(out)])==0 and out.exists()
