#!/usr/bin/env python3
"""Validate offline TPEx landing/data authority separation and immutable history."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.phase_j_b04_a6_sm_b1_r3_tpex_contract import CAPTURE_SHA256, CAPTURE_SIZE, discovery_proposal, verified_capture

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    record = json.loads((ROOT/'docs/governance/phase_j/PHASE_J_J_B04_A6_SM_B1_R3_TPEX_LIFECYCLE_SOURCE_CONTRACT_2026-10-10.json').read_text())
    assert record['starting_head'] == '1b44851e64edff534846880c94844e0f2e1ae37a'
    assert record['starting_tree'] == '4d65363795cafb907f88795464954a68fcfaf97b'
    assert record['starting_main'] == '6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a'
    assert record['R2_independent_review_id'] == '5476929940'
    for path, digest in record['historical_evidence_sha256'].items():
        assert sha(ROOT/path) == digest, path
    # Compare R3's parser snapshot with its exact starting revision instead of
    # incorrectly requiring today's qualified R5 parser to remain unchanged.
    for path, digest in record['unchanged_parser_sha256'].items():
        historical_bytes = subprocess.check_output(
            ["git", "show", f"{record['starting_head']}:{path}"], cwd=ROOT
        )
        assert hashlib.sha256(historical_bytes).hexdigest() == digest, path
    capture = record['capture']
    assert capture['sha256'] == CAPTURE_SHA256 and capture['byte_size'] == CAPTURE_SIZE
    if (ROOT/capture['path']).exists():
        verified_capture(ROOT/capture['path'])
    manifest = json.loads((ROOT/'skills/tw-security-master-classifier/references/source-manifest.json').read_text())
    historical_source = record['manifest_correction']['after']
    assert historical_source['url'] == 'https://www.tpex.org.tw/zh-tw/mainboard/listed/delisted.html'
    assert historical_source['format'] == 'client_rendered_shell'
    assert historical_source['verification'] == 'landing_capture_verified_data_contract_unresolved'
    assert historical_source['production_automatic_acquisition'] is False
    assert historical_source['contract_state'] == 'blocked_pending_data_endpoint_qualification'
    assert historical_source['lifecycle_data_contract']['endpoint'] is None
    source = next(s for s in manifest['lifecycle_sources'] if s['id'] == 'tpex_company_delisted')
    assert source['url'] == 'https://www.tpex.org.tw/www/zh-tw/company/deListed'
    assert source['format'] == 'json'
    assert source['verification'] == 'live_all_history_single_response_qualified_2026-10-10'
    assert source['production_automatic_acquisition'] is True
    assert source['contract_state'] == 'qualified_data_contract'
    assert source['lifecycle_data_contract']['state'] == 'qualified'
    other = dict(manifest)
    other['lifecycle_sources'] = [s for s in manifest['lifecycle_sources'] if s['id'] != 'tpex_company_delisted']
    assert hashlib.sha256(json.dumps(other,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest() == record['manifest_correction']['other_manifest_content_sha256']
    inv = record['structural_inventory']
    assert (inv['table_element_count'], inv['form_count'], inv['script_element_count'], inv['inline_script_count']) == (0, 3, 14, 2)
    assert inv['embedded_json_script_blocks']['count'] == 0
    assert inv['API_PATTERN']['symbolic_reference_only'] is True
    assert inv['API_PATTERN']['declaration_present'] is False
    assert inv['API_PATTERN']['literal_value_present'] is False
    assert inv['company/deListed']['classification'] == 'SYMBOLIC_ACTION_TOKEN'
    assert inv['company/deListed']['exact_literal_occurrence_count'] == 1
    assert inv['executable_lifecycle_data_endpoint'] is None
    assert inv['lifecycle_events_generated'] == 0 and inv['lifecycle_dataset_validated'] is False
    assert discovery_proposal(inv) == record['future_discovery']
    assert record['future_discovery']['max_dispatches_total'] == 4
    assert record['future_discovery']['is_owner_authorization'] is False
    materializer = (ROOT/'scripts/m8r_06_01b_materialize_production_inputs.py').read_text()
    assert materializer.index('_require_tpex_lifecycle_data_contract(manifest)', materializer.index('def main(')) < materializer.index('dispatch_budget =', materializer.index('def main('))
    assert 'BOOTSTRAP_TPEX_LIFECYCLE_DATA_CONTRACT_UNRESOLVED' in materializer
    assert record['disposition'] == 'SM_B1_R3_BOUNDED_DISCOVERY_REQUIRED'
    assert record['bootstrap_retry'] == 'NOT_AUTHORIZED'
    assert record['network_counts'] == {'market_GET_HEAD_POST':'0/0/0','security_master_live_acquisition':0}
    assert record['canonical_state'] == {'H2':'INACTIVE','selected_executor':None,'routing':'plan_only','J-B04':'BLOCKING','Phase_J':'NOT_STARTED','MCP':6}
    status = subprocess.run([sys.executable,str(ROOT/'scripts/manage_security_master.py'),'status'],cwd=ROOT,capture_output=True,text=True,check=True)
    assert json.loads(status.stdout)['status'] == 'NOT_INITIALIZED'
    assert not (ROOT/'data/security_master/active.json').exists()
    print('J-B04-A6-SM-B1-R3 validator PASS')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
