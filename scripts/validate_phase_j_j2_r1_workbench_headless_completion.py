#!/usr/bin/env python3
"""Network-free verification of additive J2-R1 browser acceptance evidence.

J1 is the only coverage baseline. Historical J2 candidates are immutable input
observations, never applied as an accepted overlay.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
START = '74772af61780f637f859eaad453c6e147fc83fc6'
START_TREE = '2bfe71203ccdf6663fc6368183847ac8f50d4157'
MAIN = '6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a'
AUTH = '21b6ede3068ec6aa139e4db6655e0e17540eda6c72f04b0fc824c219802a28f8'
REGISTRY = 'docs/governance/phase_j/PHASE_J_J0_J1_GOVERNED_SCENARIO_REGISTRY_V1.json'
MATRIX = 'docs/governance/phase_j/PHASE_J_J0_J1_COVERAGE_MATRIX_V1.json'
REGISTRY_SHA = 'b26712d1389b904ff003b22aa135caac43ab8f6fc7b32dad571b70438248c864'
MATRIX_SHA = '5d07ab2618e6bfa6c79f796df28cd69df5c105fb8f60396c293675737febcd45'
PREFIX = 'docs/governance/phase_j/PHASE_J_J2_R1_'
DELTA = PREFIX+'COVERAGE_DELTA_V1.json'
EFFECTIVE = PREFIX+'EFFECTIVE_COVERAGE_MATRIX_V1.json'
LEDGER = PREFIX+'WORKBENCH_HEADLESS_EXECUTION_LEDGER_V1.json'
GOVERNANCE = PREFIX+'WORKBENCH_HEADLESS_CROSS_LAYER_COMPLETION_2026-10-11.json'
TARGETS = ['J1-01','J1-07','J1-08','J1-10','J1-11','J1-12','J1-13','J1-14','J1-16','J1-18','J1-20','J1-22','J1-23','J1-24','J1-25','J1-26','J1-27']
KINDS = {'integration':'integration_test','service_api':'service_test','workbench':'workbench_test','mcp':'mcp_test','fresh_install':'fresh_install_test'}

def require(condition, message):
    if not condition: raise ValueError(message)

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    def pairs(items):
        result = {}
        for key,value in items:
            require(key not in result, f'duplicate key: {key}')
            result[key]=value
        return result
    return json.loads(Path(path).read_text(),object_pairs_hook=pairs)

def git(*args): return subprocess.check_output(['git',*args],cwd=ROOT,text=True).strip()

def derive(baseline, delta):
    effective = copy.deepcopy(baseline)
    rows = {row['scenario_id']:row for row in effective['scenarios']}
    seen = set()
    for promotion in delta['promotions']:
        scenario,layer = promotion['scenario_id'],promotion['layer']
        require(scenario in TARGETS and layer in KINDS, 'unapproved scenario/layer')
        require((scenario,layer) not in seen,'duplicate promotion')
        seen.add((scenario,layer))
        cell = rows[scenario]['layers'][layer]
        require(cell['status']==promotion['baseline_status']=='PLANNED','promotion baseline mismatch')
        require(promotion['new_status']=='COVERED_EXISTING','unapproved coverage status')
        require(promotion['introduced_by_tranche']=='PHASE_J_J2_R1','missing provenance')
        require(promotion['evidence_refs'],'missing layer execution evidence')
        for evidence in promotion['evidence_refs']:
            require(evidence['kind']==KINDS[layer],'layer evidence laundering')
            require('::' in evidence['ref'],'exact test node missing')
            require(scenario in evidence['ref'] or layer=='fresh_install','scenario test node mismatch')
            require((ROOT/evidence['ref'].split('::')[0]).is_file(),'test evidence missing')
            require(evidence['scenario_match'],'scenario-match explanation missing')
        cell.update(status=promotion['new_status'],evidence_refs=promotion['evidence_refs'],introduced_by_tranche='PHASE_J_J2_R1')
    effective['authority_status']='J2_R1_FROZEN_ACCEPTANCE_CANDIDATE_PENDING_REVIEW'
    effective['baseline_binding']={'matrix':MATRIX,'sha256':MATRIX_SHA,'review':'5481271339','delta':DELTA}
    counts=Counter(c['status'] for row in effective['scenarios'] for c in row['layers'].values())
    effective['coverage_summary']={'status_counts':{status:counts[status] for status in baseline['coverage_statuses']},'promoted_cell_count':len(seen)}
    return effective

def validate_implementation():
    require(git('rev-parse',START+'^{tree}')==START_TREE,'starting tree mismatch')
    require(git('rev-parse','origin/main')==MAIN,'main mismatch')
    require(sha(ROOT/REGISTRY)==REGISTRY_SHA,'J1 registry changed')
    require(sha(ROOT/MATRIX)==MATRIX_SHA,'J1 matrix changed')
    historical = [p for p in git('ls-tree','-r','--name-only',START,'docs/governance/phase_j').splitlines() if 'PHASE_J_J2_' in p]
    for path in historical:
        original=subprocess.check_output(['git','show',START+':'+path],cwd=ROOT)
        require((ROOT/path).read_bytes()==original,'historical J2 evidence changed: '+path)
    changed=git('diff','--name-only',START).splitlines()
    require(not any(p.startswith(('server/','frontend/','schemas/','config/','skills/','docs/data_capabilities/')) for p in changed),'production/public contract changed')
    from server.unified_mcp.tool_contracts import build_tool_contract_snapshot
    require([t.name for t in build_tool_contract_snapshot().tools]==['market_describe_capabilities','market_validate_request','market_preview_request','market_read_result','market_export_ai_handoff','market_fetch_evidence'],'MCP drift')
    return {'immutable_J1':True,'historical_J2_immutable':True,'production_change_count':0,'MCP':6}

def validate_evidence():
    result=validate_implementation()
    delta,effective,ledger,governance=[read(ROOT/p) for p in (DELTA,EFFECTIVE,LEDGER,GOVERNANCE)]
    require(delta['baseline_registry_sha256']==REGISTRY_SHA and delta['baseline_matrix_sha256']==MATRIX_SHA,'overlay uses unaccepted baseline')
    require(delta['baseline_review']=='5481271339','wrong J1 review')
    require(effective==derive(read(ROOT/MATRIX),delta),'effective matrix divergence')
    require(governance['owner_authorization_sha256']==AUTH,'authorization hash drift')
    require(hashlib.sha256(governance['owner_authorization_statement'].encode()).hexdigest()==AUTH,'authorization statement mismatch')
    require(governance['predecessor_review']=='5481633888','wrong predecessor review')
    require(governance['bounded_live_authorization']==governance['real_agent_authorization']=='NOT_GRANTED','unauthorized activity')
    require(governance['Phase_J']=='STARTED' and governance['Phase_K']=='NOT_STARTED','phase drift')
    require(governance['host_selector_before']==governance['host_selector_after'],'host selector changed')
    require(governance['default_ci']['candidate_only_failure_nodes']==[],'CI expanded failure set')
    rows=ledger['scenarios']
    require([r['scenario_id'] for r in rows]==TARGETS,'17 target adjudications missing')
    for row in rows:
        require(row['external_browser_request_count']==0 and row['additional_execution_count']==0,'unexpected network/reexecution')
        require(row['external_market_GET']==row['external_market_HEAD']==row['external_market_POST']==0,'market acquisition')
        require(row['browser']=='headless_chromium' and row['browser_local_request_count']>0,'real DOM browser evidence missing')
        require(row['dom_observations'] and row['test_node_ids'],'scenario DOM evidence absent')
        if row['classification']=='PREEXECUTION_FAIL_CLOSED':
            require(row['result_id'] is None and row['execute_once_request_count']==0,'fabricated refusal result/execution')
        else:
            require(row['result_id']==row['audit_result_id']==row['handoff_result_id'],'result/audit/handoff mismatch')
            require(row['execute_once_request_count']==1,'execution not single use')
    baseline=read(ROOT/MATRIX)
    for original,current in zip(baseline['scenarios'],effective['scenarios']):
        for layer in ('bounded_live','real_agent'):
            require(original['layers'][layer]==current['layers'][layer],'unauthorized coverage promotion')
    result.update(scenarios=len(rows),promotions=len(delta['promotions']))
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--implementation-only',action='store_true');args=parser.parse_args()
    print(json.dumps(validate_implementation() if args.implementation_only else validate_evidence(),indent=2))
