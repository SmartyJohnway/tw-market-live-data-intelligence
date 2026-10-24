from pathlib import Path
import os,sys,json,subprocess

ROOT=Path(r'C:\twmarket_temp\l7-a2\repo')
OUT=Path(r'C:\twmarket_temp\l7-a2\continuation\final-checks')
OUT.mkdir(exist_ok=False)
for name in ('home','state','local','temp'):(OUT/name).mkdir()
os.chdir(ROOT);sys.path.insert(0,str(ROOT))
os.environ.update(TW_MARKET_CI_NODE=r'C:\Program Files\nodejs\node.exe',TW_MARKET_CI_BOUND=r'C:\twmarket_temp\l7-a2',TW_MARKET_CI_GUARD_LOG=str(OUT/'guard.jsonl'),TW_MARKET_HOME=str(OUT/'home'),TW_MARKET_STATE_ROOT=str(OUT/'state'),LOCALAPPDATA=str(OUT/'local'),TEMP=str(OUT/'temp'),TMP=str(OUT/'temp'),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',TW_MARKET_ACCEPTANCE_GUARD_BASE=r'C:\twmarket_temp\l7-a2',TW_MARKET_GUARD_LOG=str(OUT/'native-guard.jsonl'))
os.environ.pop('PYTEST_ADDOPTS',None)
for key in list(os.environ):
    if key.lower() in ('http_proxy','https_proxy','all_proxy'):os.environ.pop(key)
from scripts.deterministic_ci_guard import install
install()
results=[]
def run(label,cmd):
    p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=180)
    results.append({'validator':label,'command':cmd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    (OUT/'results.json').write_bytes((json.dumps(results,indent=2)+'\n').encode())
    print(label,p.returncode,flush=True)
    return p
for name in ('validate_v1_front_door','governance_forbidden_path_guard','validate_product_version_consistency','validate_release_hygiene','validate_runtime_skill_guide_sync','validate_v1_public_contracts','validate_github_actions_execution_policy','validate_l7_a2_workflow_policy'):
    run(name,[sys.executable,'-B','scripts/'+name+'.py'])
run('workflow_and_packaging_unit_tests',[sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider','--basetemp='+str(OUT/'pytest-temp'),'--junitxml='+str(OUT/'report.xml'),'tests/unit/test_github_actions_execution_policy.py','tests/unit/test_l7_a2_workflow_policy.py','tests/unit/test_l7_a2_source_admission.py','tests/unit/test_l7_a2_docker_acceptance_guard.py','tests/unit/test_l6_a4_docker_packaging.py','tests/unit/test_l6_a4_docker_network_profile.py'])
bundle=Path(r'C:\twmarket_temp\l7-a2\continuation\final-source\native-quiet\Location-B\TW-Market-1.0.0-windows-x64')
code="""import sys,json,hashlib,importlib.util
from pathlib import Path
import jsonschema
bundle=Path(BUNDLE)
spec=importlib.util.spec_from_file_location('a2_integrity',bundle/'bootstrap/package_integrity.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);report=module.verify_bundle(bundle)
schemas={p.name:json.loads(p.read_text(encoding='utf-8')) for p in (bundle/'app/schemas').glob('*.schema.json')}
for schema in schemas.values():jsonschema.validators.validator_for(schema).check_schema(schema)
request={'schema_version':'unified_market_evidence_request.v3','request_id':'a2-packaged-preservation','targets':[{'input':'2330','market_hint':'TWSE'}],'data_needs':[{'type':'identity','priority':'required'}],'execution_mode':'preview'}
name=next(n for n in schemas if n.startswith('unified_market_evidence_request') and '.v3.' in n)
jsonschema.validate(request,schemas[name])
print(json.dumps({'status':'PASS_AS_PRESERVATION','FINAL_L7_ACCEPTANCE':'DEFERRED','source_commit':report['manifest']['source_commit'],'manifested_member_count':report['manifest']['member_count'],'checked_schema_count':len(schemas),'representative_request_v3_valid':True,'checked_schemas':sorted(schemas),'sys_path':sys.path,'executable':sys.executable}))
""".replace('BUNDLE',repr(str(bundle)))
run('packaged_integrity_and_public_schema_preservation',[str(bundle/'runtime/venv/Scripts/python.exe'),'-I','-B','-c',code])
for path in (ROOT/'scripts').glob('*.py'):compile(path.read_bytes(),str(path),'exec')
results.append({'validator':'script_syntax_static','exit_code':0})
events=[json.loads(s) for s in (OUT/'guard.jsonl').read_text().splitlines()]
denials=[v for v in events if v['event']=='denied']
(OUT/'summary.json').write_bytes((json.dumps({'status':'PASS' if not denials and all(v['exit_code']==0 for v in results) else 'FAIL','guard_denials':denials,'results':results},indent=2)+'\n').encode())
raise SystemExit(bool(denials) or any(v['exit_code'] for v in results))
