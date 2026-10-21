"""Real six-tool lifecycle, actual child/adapters, bounded fixture transport only."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import validate_l5_integrated_extension_contract_acceptance as a6


@pytest.fixture(scope='module')
def evidence(tmp_path_factory):
    e = a6.build_evidence(tmp_path_factory.mktemp('a6-integration'))
    capture = os.environ.get('L5_A6_ACCEPTANCE_CAPTURE')
    if capture:
        Path(capture).write_text(json.dumps(e, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    return e


@pytest.mark.parametrize('key',['twse','tpex','mixed_outcome'])
def test_actual_governed_six_tool_trace(evidence,key):
    t=evidence['traces'][key]
    assert a6.validate_trace(t)==[]
    assert len(evidence['graphs'][key]['nodes'])==25
    assert len(evidence['graphs'][key]['edges'])==24
    assert all(x['result']=='PASS' for x in evidence['graphs'][key]['edges'])
    assert t['public_rejections']['request_changed_after_preview']['http_status'] != 200


@pytest.mark.parametrize('key',['twse','tpex'])
def test_repeat_semantic_determinism(evidence,key):
    row=evidence['determinism'][key]
    assert row['first']==row['second']
    assert row['first_semantic_sha256']==row['second_semantic_sha256']


def test_failure_containment_and_caveats(evidence):
    t=evidence['traces']['mixed_outcome']
    c,_,r,_=a6.parts(t)
    assert r['status']=='partially_failed'
    assert r['targets'][0]['evidence']['monthly_revenue']['value']['current_month_revenue']==100
    assert r['targets'][0]['evidence']['material_disclosures']['status']=='source_failed'
    assert 'source_failed' in c['market_export_ai_handoff']['ai_ready_markdown']
    assert 'all_governed_transports_failed' in c['market_export_ai_handoff']['ai_ready_markdown']


@pytest.mark.parametrize('mutation',[
    'request_changed_after_preview','request_extra_field','preview_capability','executor','market',
    'source_contract','operation_contract','typed_contract','artifact_hash','citation_operation','citation_target',
    'result_hash','audit_hash','audit_lineage','handoff_invention','seventh_tool','unexpected_socket',
])
def test_trace_mutations_fail_closed(evidence,mutation):
    t=deepcopy(evidence['traces']['twse'])
    c,a,r,audit=a6.parts(t)
    op=a['control/plan.json']['operations'][0]
    typed=r['targets'][0]['evidence']['monthly_revenue']
    operation=next(v for k,v in a.items() if k.startswith('evidence/') and v['capability_id']=='monthly_revenue')
    if mutation=='request_changed_after_preview': t['request']['request_id']='mutated'
    elif mutation=='request_extra_field': t['request']['data_needs'][0]['capability_id']='monthly_revenue'
    elif mutation=='preview_capability': c['market_preview_request']['orchestration_plan']['operations'][0]['capability_id']='material_disclosures'
    elif mutation=='executor': op['executor_id']='unknown_executor'
    elif mutation=='market': op['market']='TPEX'
    elif mutation=='source_contract': operation['source']['source_contract_id']='t187ap04_L'
    elif mutation=='operation_contract': operation['schema_version']='phase_g_material_disclosure_operation_evidence.v1'
    elif mutation=='typed_contract': typed['schema_version']='material_disclosure_evidence.v1'
    elif mutation=='artifact_hash': audit['operation_lineage'][0]['artifact_references'][0]['sha256']='0'*64
    elif mutation=='citation_operation': audit['citation_to_operation_map'][0]['operation_id']='wrong-operation'
    elif mutation=='citation_target': audit['citation_to_operation_map'][0]['canonical_target_id']='TPEX:6488'
    elif mutation=='result_hash': typed['value']['current_month_revenue']=999
    elif mutation=='audit_hash': audit['result_hash']='0'*64
    elif mutation=='audit_lineage': audit['operation_lineage'][0]['executor_id']='wrong-executor'
    elif mutation=='handoff_invention': c['market_export_ai_handoff']['ai_ready_markdown']+='\nInvented conclusion cite-fake\n'
    elif mutation=='seventh_tool': t['tool_names'].append('extension_tool')
    elif mutation=='unexpected_socket': t['socket_attempts'].append('198.51.100.1')
    assert a6.validate_trace(t), mutation


@pytest.mark.parametrize('mutation',['catalog','routing','portable','family_registry','new_capability',
                                    'retention','security','resource','missing_dimension'])
def test_authority_mutations_fail_closed(evidence,mutation):
    s=deepcopy(evidence['publication'])
    if mutation=='catalog': s['catalog']['data_need_capabilities'][0]['support_status']='runtime_executable'
    elif mutation=='routing': s['routing']['routes'][0]['selected_executor_id']='unknown'
    elif mutation=='portable': s['portable']['portable_metadata']['generated_from_commit']='0'*40
    elif mutation=='new_capability':
        s['catalog']['data_need_capabilities'].append({'capability_id':'financial_statements'})
    elif mutation=='family_registry': s['family_registry']={'fake':'family'}
    elif mutation in ('retention','security','resource'): s['family_owned_policies']=[mutation]
    elif mutation=='missing_dimension': s['dimensions'].pop()
    assert a6.validate_context(s), mutation


def test_36_dimensions_and_publication(evidence):
    assert evidence['status']=='PASS',evidence['errors']
    assert len(evidence['dimensions'])==36
    assert len({d['dimension_id'] for d in evidence['dimensions']})==36
    assert not evidence['publication']['errors']
    assert all(d['frozen_a1_classification']!='DECISION_REQUIRED' for d in evidence['dimensions'])


def test_child_socket_guard_rejects_before_dispatch(tmp_path):
    # Intentional guard self-test, separate from primary trace network counts.
    code="from tests.helpers.l5_a6_source_transport import install; install(); import socket; socket.create_connection(('198.51.100.1',9))"
    env=os.environ|{'M8R_06_03_EXECUTION_ENVIRONMENT':'test','M8R_06_03_TEST_SOURCE_TRANSPORT':'deterministic','PYTHONUTF8':'1'}
    r=subprocess.run([sys.executable,'-B','-c',code],cwd=a6.ROOT,env=env,capture_output=True,text=True)
    assert r.returncode!=0
    assert 'A6_UNEXPECTED_CHILD_SOCKET:socket.getaddrinfo' in r.stderr


def test_protected_product_authorities_unchanged():
    paths=['server','schemas','config','docs/data_capabilities','scripts/phase_g','scripts/m8r_05c',
           'scripts/m8r_06_03_execute_once.py','scripts/m8r_06_03_production_adapter.py',
           'skills','requirements.txt','pyproject.toml']
    result=subprocess.check_output(['git','diff','928de0f930b0733e188ef3c873f994ce9e8a69d3','--name-only','--',*paths],cwd=a6.ROOT,text=True)
    assert result.strip()==''
