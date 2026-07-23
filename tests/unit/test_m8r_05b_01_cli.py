import json,copy
from pathlib import Path
from scripts.m8r_05b_01.cli import main
from tests.unit.test_m8r_05b_01_planner import validation,bindings,CAT,ROUTE,HAND,INV

def test_check_only_and_output(tmp_path):
 v=validation(); paths={}
 for key,value in {'v':v,'c':CAT,'r':ROUTE,'h':HAND,'i':INV,'b':bindings(v)}.items():
  p=tmp_path/(key+'.json');p.write_text(json.dumps(value));paths[key]=p
 args=['--validation-input',str(paths['v']),'--capability-catalog',str(paths['c']),'--routing-matrix',str(paths['r']),'--handoff-contract',str(paths['h']),'--executor-disposition',str(paths['i']),'--input-bindings',str(paths['b']),'--planning-timestamp','2026-07-23T00:00:00Z','--check-only']
 assert main(args)==0 and not (tmp_path/'out.json').exists()
 assert main(args[:-1]+['--output',str(tmp_path/'out.json')])==0
 assert json.loads((tmp_path/'out.json').read_text())['execution_authorized'] is False
def test_bad_json_has_deterministic_error(tmp_path):
 p=tmp_path/'bad.json';p.write_text('{')
 assert main(['--validation-input',str(p),'--capability-catalog',str(p),'--routing-matrix',str(p),'--handoff-contract',str(p),'--executor-disposition',str(p),'--input-bindings',str(p),'--planning-timestamp','bad','--check-only'])==2
