import json, pathlib

def test_final_acceptance_and_registry_state():
    text=pathlib.Path('docs/protocol/M8C_00_TAIFEX_MIS_PREFLIGHT_FINAL_ACCEPTANCE.md').read_text()
    assert 'm8c_00_taifex_mis_preflight_pass_with_caveats' in text
    assert 'M8C-01-TAIFEX-MIS-BOUNDED-REST-SOCKJS-SNAPSHOT-RUNTIME' in text
    reg=json.loads(pathlib.Path('docs/data_capabilities/m8_source_capability_registry.json').read_text())
    s=[x for x in reg['sources'] if x['source_id']=='TAIFEX_MIS'][0]
    assert s['runtime_executable'] is True
    assert s['adapter_implemented'] is True
    assert s['runtime_status']=='bounded_initial_state_snapshot_runtime_implemented_pending_m8c_02_integration'
    assert s['ai_context_allowed'] is False
    assert s['preflight_transport_reproduced'] is True

def test_no_raw_probe_payloads_committed():
    for path in pathlib.Path('research/probe_runs/m8c_taifex_mis_preflight').glob('*.json'):
        data=json.loads(path.read_text())
        assert data['raw_payload_retained'] is False
        assert data['cookies_retained'] is False
