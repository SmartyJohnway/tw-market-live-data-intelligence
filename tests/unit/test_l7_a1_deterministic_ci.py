"""Current blocking equivalents for retained historical scope assertions."""
import copy
import json
from pathlib import Path
import subprocess
import os
import socket
import sys
import time
from urllib.request import Request,urlopen
from urllib.error import URLError

import pytest
from scripts import run_test_profile

ROOT=Path(__file__).resolve().parents[2]


def contract():
    return json.loads((ROOT/'config/release_blocking_ci.v1.json').read_text(encoding='utf-8'))


def current_authorities():
    return {p:json.loads((ROOT/p).read_text(encoding='utf-8')) for p in contract()['public_authorities']}


def accepted_authorities():
    c=contract()
    return {p:json.loads(subprocess.check_output(['git','show',c['public_authority_anchor']+':'+p],cwd=ROOT).decode('utf-8')) for p in c['public_authorities']}


def assert_current_authorities(current):
    assert current==accepted_authorities(), 'current public/source/route authority drift requires explicit governance'


def test_current_public_authorities_match_accepted_entry():
    # Unlike old "no later source change" gates, this binds current accepted
    # capability/source/executor authority, not obsolete production source text.
    assert_current_authorities(current_authorities())


@pytest.mark.parametrize('surface',contract()['public_authorities'])
def test_current_authority_mutation_is_detected(surface):
    changed=copy.deepcopy(current_authorities())
    changed[surface]['unapproved_seventh_tool_or_family']='forbidden'
    with pytest.raises(AssertionError,match='authority drift'):
        assert_current_authorities(changed)


def test_historical_scope_nodes_are_explicit_and_preserved():
    c=contract()
    assert len(c['historical_diagnostics'])==15
    for node,row in c['historical_diagnostics'].items():
        module,name=node.split('::',1)
        assert ('def '+name.split('[')[0]+'(') in (ROOT/module).read_text(encoding='utf-8')
        assert row['current_equivalent_coverage'] and row['historical_evidence_retained']


def test_current_phase_j_closure_retains_accepted_k_continuation():
    # The historical validator additionally demanded K NOT_STARTED. Later K
    # acceptance is legitimate; do not revive that frozen readiness condition.
    source=ROOT/'docs/governance/phase_j/PHASE_J_CLOSURE_AUTHORITY_RECONCILIATION_2026-10-12.json'
    closure=json.loads(source.read_text(encoding='utf-8'))
    assert closure['disposition']=='PHASE_J_CLOSURE_AUTHORITY_RECONCILIATION_PASS'
    assert closure['phase_state']['phase_j']=='COMPLETE'
    assert closure['phase_state']['remaining_obligations']==[]
    assert closure['attempt6_adjudication']['real_agent_layer_satisfied'] is True
    assert 'PHASE_K_OWNER_ACCEPTED_FINAL_CLOSURE_PASS' in (ROOT/'docs/governance/phase_k/PHASE_K_FINAL_OWNER_ACCEPTANCE_AND_CLOSURE_2026-10-13.md').read_text(encoding='utf-8')
    assert '# [x] Phase J — Integrated Research Acceptance' in (ROOT/'ROADMAP.md').read_text(encoding='utf-8')


def test_profile_routes_to_one_guarded_contract_and_requires_fresh_output(tmp_path):
    commands=run_test_profile.resolve_profile('release-blocking-ci',output_root=tmp_path)
    assert len(commands)==1
    assert 'scripts/run_deterministic_ci.py' in commands[0]
    assert commands[0][-2:]==['--output-root',str(tmp_path/'release-blocking-ci')]


def test_canonical_profile_timeout_is_a_failure(monkeypatch):
    def timeout(*args,**kwargs):
        assert kwargs['timeout']==3600
        raise subprocess.TimeoutExpired(args[0],3600,output=b'partial evidence')
    monkeypatch.setattr(run_test_profile.subprocess,'run',timeout)
    rows=run_test_profile.run_commands([{'command':['python','scripts/run_deterministic_ci.py'],'execution_kind':'authoritative_runner'}],capture=True)
    assert rows[0]['return_code']==124
    assert 'hard deadline exceeded' in rows[0]['_output']


def test_output_boundary_is_checked_before_creating_directories(tmp_path,monkeypatch):
    from scripts import run_deterministic_ci as runner
    monkeypatch.setattr(runner,'ROOT',tmp_path/'isolated/repo')
    outside=tmp_path/'outside'
    with pytest.raises(ValueError,match='isolated workspace parent'):
        runner.main(['--output-root',str(outside)])
    assert not outside.exists()


def test_current_72_cell_family_equivalent_checks_semantics_offline(monkeypatch):
    """Keep current semantic proofs without the old no-post-L5-source-change gate."""
    import socket
    from scripts.validate_l5_existing_family_conformance import dimension_matrix, build_case, validate_case
    def deny(*args,**kwargs):raise AssertionError('no real transport in current equivalent')
    monkeypatch.setattr(socket.socket,'connect',deny)
    monkeypatch.setattr(Path,'write_text',deny)
    monkeypatch.setattr(Path,'write_bytes',deny)
    assert len(dimension_matrix())==72
    assert {r['applicability'] for r in dimension_matrix()}=={'APPLICABLE'}
    for family in ['monthly_revenue','material_disclosures']:
        for market in ['TWSE','TPEX']:
            for status in ['available','missing','source_failed']:
                case=build_case(family,market,status)
                assert validate_case(case)==[]
                corrupt=copy.deepcopy(case)
                corrupt['operation_evidence']['capability_id']='unapproved_family'
                assert validate_case(corrupt)


def test_explicit_offline_release_serves_identity_over_real_localhost(tmp_path):
    """Current witness replaces dependence on an ignored developer sealed bundle."""
    from scripts.tw_market_installation import initialize_installation
    from scripts.m8r_08g_security_master_releases import build_candidate_release,qualify_candidate_release,activate_qualified_release
    inst=initialize_installation(home=tmp_path/'home',state_root=tmp_path/'state',environ={'LOCALAPPDATA':str(tmp_path/'local')})
    root=inst.security_master_root
    record={'canonical_target_id':'TWSE:2330','identity':{'security_code':'2330','isin':'TW0002330008'},'classification':{'market':'TWSE','instrument_family':'company_share','instrument_type':'common_share'},'lifecycle':{'state':'listed','resolution_status':'resolved','basis_event_ids':[],'events':[]},'execution_eligibility':{'status':'allowed','reason_codes':[]}}
    rid='security-master-20261024T000000Z'
    build_candidate_release(root=root,release_id=rid,records=[record],source_provenance={'source_type':'deterministic_test_fixture','snapshot_id':'a1-localhost','source_content_hashes':{'synthetic':'a'*64},'producer_skill':{'name':'test','skill_version':'1','skill_contract_hash':'b'*64}})
    qualified,report=qualify_candidate_release(root=root,release_id=rid)
    assert qualified and report['status']=='PASS'
    activate_qualified_release(root=root,release_id=rid)
    with socket.socket() as probe:
        probe.bind(('127.0.0.1',0));port=probe.getsockname()[1]
    env=os.environ|{'TW_MARKET_HOME':str(inst.home),'TW_MARKET_STATE_ROOT':str(inst.state_root),'TW_MARKET_SECURITY_MASTER_ROOT':str(root),'TW_MARKET_OPERATIONAL_EVENT_PATH':str(tmp_path/'events.jsonl')}
    process=subprocess.Popen([sys.executable,'scripts/run_unified_workbench.py','--port',str(port)],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        base=f'http://127.0.0.1:{port}';deadline=time.monotonic()+30
        while True:
            try:
                with urlopen(base+'/api/health',timeout=2) as response:assert response.status==200
                break
            except URLError:
                if time.monotonic()>deadline:raise AssertionError('initialized offline service did not become healthy')
                time.sleep(.1)
        req={'schema_version':'unified_market_evidence_request.v3','request_id':'a1-offline-identity','execution_mode':'preview','targets':[{'input':'2330','market_hint':'TWSE'}],'data_needs':[{'type':'current_observation','priority':'required'}]}
        with urlopen(Request(base+'/api/unified/validate-request',data=json.dumps({'request':req}).encode(),headers={'Content-Type':'application/json'}),timeout=10) as response:
            result=json.load(response)
            assert response.status==200 and result['validation_status']=='valid'
    finally:
        process.terminate()
        try:process.wait(timeout=10)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=10)
