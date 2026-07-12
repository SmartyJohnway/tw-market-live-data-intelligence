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
