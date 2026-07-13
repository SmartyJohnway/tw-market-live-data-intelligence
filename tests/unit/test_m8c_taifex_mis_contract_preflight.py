import json, pathlib

def test_transport_registry_preflight_not_runtime():
    d=json.loads(pathlib.Path('docs/data_capabilities/m8c_taifex_mis_transport_registry.json').read_text())
    assert d['push_transport']['primary_bounded_candidate']=='xhr_polling'
    assert d['push_transport']['websocket_runtime_reproduced'] is False
    assert d['messages']['unsubscribe_verified'] is False
    assert d['raw_payload_retained'] is False

def test_option_scope_not_exact_network_scope():
    d=json.loads(pathlib.Path('docs/data_capabilities/m8c_taifex_mis_rest_endpoint_registry.json').read_text())
    assert d['option_discovery']['network_scope']=='whole_requested_contract_month_chain'
    assert 'exact requested' in d['option_discovery']['retained_scope']
    assert d['option_discovery']['raw_payload_retained'] is False
import csv

def test_capability_true_has_evidence_artifact():
    evidence=json.loads(pathlib.Path('research/probe_runs/m8c_taifex_mis_preflight/sockjs_initial_state_summary.json').read_text())
    observed={q['symbol'] for q in evidence['quotes']}
    assert evidence['status']=='successful_initial_state_probe'
    with pathlib.Path('docs/data_capabilities/m8c_taifex_mis_product_capability_matrix.csv').open() as f:
        for row in csv.DictReader(f):
            if row['initial_push_verified']=='true':
                assert any(i['requested_product_id']==row['requested_product_id'] and i['runtime_symbol_id'] in observed for i in json.loads(pathlib.Path('research/probe_runs/m8c_taifex_mis_preflight/identity_resolution_summary.json').read_text())['identities'])
            if row['regular_session_verified']=='true' or row['after_hours_verified']=='true':
                raise AssertionError('session verification cannot be true without active-session evidence')

def test_rest_scoped_evidence_not_empty_body_probe():
    d=json.loads(pathlib.Path('research/probe_runs/m8c_taifex_mis_preflight/rest_endpoint_probe_summary.json').read_text())
    assert d['endpoints']['getQuoteList_TXF_202607']['row_count']==1
    assert d['endpoints']['getQuoteListOption_RowSize_PageNo_variant']['row_size_page_reduced_network_response'] is False
    assert d['endpoints']['getQuoteListOption_StrikePrice_CP_variant']['strike_cp_reduced_network_response'] is False
