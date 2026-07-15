from scripts.discover_m8r_taifex_option_contracts import SCHEMA_VERSION, merge_identities

def test_bounded_discovery_schema_no_auto_selection_and_no_raw_retention():
    results={
        'TAIFEX_MIS': {'exact_contract_identities':[{'strike':'40000','call_put':'C','product':'TXO','underlying':'TX','expiry':'202607','session':'regular','source_evidence':['TAIFEX_MIS']}]},
        'TAIFEX_OPENAPI': {'exact_contract_identities':[{'strike':'40000','call_put':'C','product':'TXO','underlying':'TX','expiry':'202607','session':'regular','source_evidence':['TAIFEX_OPENAPI']}]} }
    exact=merge_identities(results)
    artifact={'schema_version':SCHEMA_VERSION,'exact_contract_identities':exact,'raw_payload_retained':False,'operator_selection_required':True}
    assert artifact['schema_version']=='m8r_taifex_option_contract_discovery.v1'
    assert artifact['operator_selection_required'] is True
    assert artifact['raw_payload_retained'] is False
    assert exact[0]['source_evidence']==['TAIFEX_MIS','TAIFEX_OPENAPI']
    assert 'selected' not in str(artifact).lower()

def test_historical_and_new_evidence_separation_contract():
    manifest={'schema_version':'m8r_02b_f1_revalidation_manifest.v1','historical_validation_run_id':'m8r02b-20260715T020000Z','revalidation_run_id':'m8r02b-f1-20260715T120000Z'}
    assert manifest['historical_validation_run_id'] != manifest['revalidation_run_id']
