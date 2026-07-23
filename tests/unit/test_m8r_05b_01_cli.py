import json,copy
from pathlib import Path
import jsonschema,pytest
from scripts.m8r_05b_01.cli import main
from tests.unit.test_m8r_05b_01_planner import validation,bindings,CAT,ROUTE,HAND,INV
SCHEMA=json.load(open('schemas/unified_market_evidence_orchestration_plan.v1.schema.json'))
def files(tmp):
 v=validation();out={}
 for k,x in {'v':v,'c':CAT,'r':ROUTE,'h':HAND,'i':INV,'b':bindings(v)}.items():
  p=tmp/(k+'.json');p.write_text(json.dumps(x));out[k]=p
 return out
def argv(p,extra=()): return ['--validation-input',str(p['v']),'--capability-catalog',str(p['c']),'--routing-matrix',str(p['r']),'--handoff-contract',str(p['h']),'--executor-disposition',str(p['i']),'--input-bindings',str(p['b']),'--planning-timestamp','2026-07-23T00:00:00Z',*extra]
def error(capsys):
 x=capsys.readouterr().err.strip().splitlines();assert len(x)==1;return json.loads(x[0])['error_code']
def test_success_schema_and_check_only_preserves(tmp_path,capsys):
 p=files(tmp_path);old=tmp_path/'old';old.write_bytes(b'old');assert main(argv(p,['--check-only']))==0 and old.read_bytes()==b'old' and not capsys.readouterr().err
 out=tmp_path/'plan.json';assert main(argv(p,['--output-root',str(tmp_path),'--output-relative','plan.json']))==0;v=json.loads(out.read_text());jsonschema.Draft7Validator(SCHEMA,format_checker=jsonschema.FormatChecker()).validate(v);assert v['execution_authorized'] is False
def test_output_contract_errors(tmp_path,capsys):
 p=files(tmp_path)
 for extra in ([],['--output-root',str(tmp_path)],['--output-relative','x'],['--check-only','--output-root',str(tmp_path)],['--check-only','--output-relative','x'],['--output-root',str(tmp_path),'--output-relative','/x'],['--output-root',str(tmp_path),'--output-relative','../x']):
  assert main(argv(p,extra))==2;assert error(capsys) in {'output_path_forbidden','rooted_output_path_forbidden','path_traversal_forbidden'}
def test_planning_failure_preserves_output(tmp_path,capsys):
 p=files(tmp_path);out=tmp_path/'plan';out.write_bytes(b'old');p['b'].write_text(json.dumps({**bindings(validation()),'capability_catalog_hash':'0'*64}))
 assert main(argv(p,['--output-root',str(tmp_path),'--output-relative','plan']))==2;assert error(capsys)=='capability_catalog_hash_mismatch' and out.read_bytes()==b'old'
def test_symlink_and_directory_rejected(tmp_path,capsys):
 p=files(tmp_path);outside=tmp_path/'outside';outside.write_text('x');link=tmp_path/'link'
 try: link.symlink_to(outside)
 except OSError: pytest.skip('symlink unavailable')
 assert main(argv(p,['--output-root',str(tmp_path),'--output-relative','link']))==2;assert error(capsys) in {'output_destination_symlink_forbidden','output_path_forbidden'};assert outside.read_text()=='x'
 assert main(argv(p,['--output-root',str(tmp_path),'--output-relative','.']))==2;assert error(capsys) in {'output_path_forbidden','atomic_replace_failed','empty_relative_path_forbidden'}
