import json
from scripts.m8r_05b_02.cli import main
from tests.unit.test_m8r_05b_02_authorization import plan,decision
def test_check_only(tmp_path):
 p=tmp_path/'p.json';d=tmp_path/'d.json';p.write_text(json.dumps(plan()));d.write_text(json.dumps(decision()));assert main(['--plan-input',str(p),'--decision-input',str(d),'--evaluation-timestamp','2026-07-23T00:30:00Z','--check-only'])==0
def test_write(tmp_path):
 p=tmp_path/'p.json';d=tmp_path/'d.json';p.write_text(json.dumps(plan()));d.write_text(json.dumps(decision()));assert main(['--plan-input',str(p),'--decision-input',str(d),'--evaluation-timestamp','2026-07-23T00:30:00Z','--output-root',str(tmp_path/'out'),'--output-relative','a.json'])==0;assert (tmp_path/'out/a.json').exists()
