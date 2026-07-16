import csv, json, pathlib

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
    assert d['option_discovery']['row_size_page_reduced_network_response'] is False
    assert d['option_discovery']['strike_cp_reduced_network_response'] is False
    assert d['option_discovery']['raw_payload_retained'] is False

def test_capability_true_has_evidence_artifact():
    evidence=json.loads(pathlib.Path('research/probe_runs/m8c_taifex_mis_preflight/sockjs_initial_state_summary.json').read_text())
    observed={q['symbol'] for q in evidence['quotes']}
    assert evidence['status']=='successful_initial_state_probe'
    assert evidence['frame_count'] == 2
    assert evidence['decoded_message_count'] == 3
    identities=json.loads(pathlib.Path('research/probe_runs/m8c_taifex_mis_preflight/identity_resolution_summary.json').read_text())['identities']
    with pathlib.Path('docs/data_capabilities/m8c_taifex_mis_product_capability_matrix.csv').open() as f:
        for row in csv.DictReader(f):
            if row['initial_push_verified']=='true':
                assert any(i['requested_product_id']==row['requested_product_id'] and i['runtime_symbol_id'] in observed for i in identities)
            if row['regular_session_verified']=='true' or row['after_hours_verified']=='true':
                raise AssertionError('session verification cannot be true without active-session evidence')

def test_rest_scoped_evidence_not_empty_body_probe():
    d=json.loads(pathlib.Path('research/probe_runs/m8c_taifex_mis_preflight/rest_endpoint_probe_summary.json').read_text())
    records=d['endpoints']
    assert any(r['endpoint_id']=='getQuoteList' and r['row_count']==1 for r in records)
    assert any(r.get('row_size_page_reduced_network_response') is False for r in records)
    assert any(r.get('strike_cp_reduced_network_response') is False for r in records)
    assert any(r['endpoint_id']=='getCalculatedFields' and r.get('status_note')=='formally_probed_with_dynamic_tx_symbol' for r in records)

def test_planning_state_has_single_next_task_and_inventory_section():
    reg=json.loads(pathlib.Path('docs/data_capabilities/m8_source_capability_registry.json').read_text())
    assert reg['next_task']=='M8R-03E-F1-AI-CAPABILITY-GUIDE-AND-AGENT-SKILL-CONTRACT'
    assert reg['next_task_status']=='accepted_successor'
    assert reg['m8_active_consolidated_status']['next_task']=='M8R-03E-F1-AI-CAPABILITY-GUIDE-AND-AGENT-SKILL-CONTRACT'
    assert reg['planning_state']['next_task']=='M8R-03E-F1-AI-CAPABILITY-GUIDE-AND-AGENT-SKILL-CONTRACT'
    inv=json.loads(pathlib.Path('docs/data_capabilities/twse_mis_rich_field_inventory.json').read_text())['m8c_00_taifex_mis_preflight']
    assert inv['runtime_adapter_implemented'] is False
    assert inv['runtime_executable'] is False
    assert inv['ai_context_allowed'] is False

def test_final_acceptance_does_not_contain_stale_counter_evidence():
    text=pathlib.Path('docs/protocol/M8C_00_TAIFEX_MIS_PREFLIGHT_FINAL_ACCEPTANCE.md').read_text()
    forbidden=['62/62','43/43','6,472','6472','85 frames','87 decoded','frames=85','decoded_messages=87']
    assert not [token for token in forbidden if token in text]
    assert '58/58' in text
    assert '36/36' in text
    assert 'frame_count=2' in text
    assert 'decoded_message_count=3' in text

def test_rest_registry_has_probe_case_ids_and_payload_byte_semantics():
    d=json.loads(pathlib.Path('docs/data_capabilities/m8c_taifex_mis_rest_endpoint_registry.json').read_text())
    assert 'response_and_send_payload_bytes' in d['byte_accounting']
    assert all(r.get('probe_case_id') for r in d['records'])
