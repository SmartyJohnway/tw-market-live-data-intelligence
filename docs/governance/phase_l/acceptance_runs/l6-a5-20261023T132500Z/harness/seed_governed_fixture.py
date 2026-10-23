"""Generate accepted sanitized Mode-C fixture state; this is seed creation only."""
import json,os,pathlib,sys
r=pathlib.Path(r'C:\twmarket_temp\l6-a5\final-run')
os.environ.update(TW_MARKET_HOME=str(r/'installations/p4-source-v2'),TEMP=str(r/'temp'),TMP=str(r/'temp'),PYTHONDONTWRITEBYTECODE='1')
sys.path.insert(0,str(pathlib.Path(r'C:\twmarket_temp\l6-a5\repo')))
os.chdir(pathlib.Path(r'C:\twmarket_temp\l6-a5\repo'))
import pytest
from tests.unit.test_m8r_06_04_mode_c import mode_c_root,PACKAGE_ID
from server.services import unified_mode_c
from scripts.tw_market_installation import initialize_installation
inst=initialize_installation(home=r/'installations/p4-source-v2')
with pytest.MonkeyPatch.context() as m:
    package=mode_c_root.__wrapped__(inst.governed_root/'fixture-input',m)
    result=unified_mode_c.build_mode_c_result_package({'control_package_id':PACKAGE_ID})
assert result['materialization']=='newly_materialized' and result['external_market_network_executed'] is False
records=[]
for p in sorted(package.rglob('*')):
    if not p.is_file():continue
    rel=p.relative_to(package).as_posix()
    if rel in {'control/request.json','control/plan.json'}:family='request_and_plan'
    elif rel in {'control/authorization.json','control/consumption_binding.json'}:family='authorization_and_consumption_binding'
    elif rel.startswith('control/'):family='finalized_control_package'
    elif rel.startswith('claims/'):family='execution_claim'
    elif rel.startswith('receipts/'):family='execution_receipt'
    elif rel.startswith('bundles/'):family='evidence_bundle'
    elif rel=='mode_c/f3_validation.json':family='f3_historical_validation_artifact'
    elif rel.startswith('operations/'):family='operation_evidence_and_source_snapshots'
    elif rel.startswith('audit/'):family='persisted_audit_package'
    elif rel.endswith('.md'):family='persisted_result_markdown'
    elif rel.startswith('ai_context/'):family='persisted_result_json'
    else:raise AssertionError('fixture member must be explicitly adjudicated: '+rel)
    records.append({'relative_path':p.relative_to(inst.governed_root).as_posix(),'family':family})
(r/'governed-fixture-members.json').write_text(json.dumps({'fixture_authority':'tests/unit/test_m8r_06_04_mode_c.py::mode_c_root','source_commit':'3707c553497240f6ff0f7e5358301395fd60205a','package_id':PACKAGE_ID,'members':records,'result':result},indent=2),encoding='utf-8')
print('accepted fixture members:',len(records))
