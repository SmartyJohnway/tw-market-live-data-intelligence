from scripts.m8c_taifex_mis_probe_common import identity_key, resolve_option_identity

def test_product_cid_symbol_distinct_and_sessions_do_not_collide():
    assert 'TX'!='TXF'!='TXFG6-F'
    assert identity_key({'runtime_symbol_id':'TXFG6-F','session':'regular','market_type':'0'}) != identity_key({'runtime_symbol_id':'TXFG6-M','session':'after_hours','market_type':'1'})

def test_option_identity_resolution_fail_closed():
    rows=[{'SymbolID':'TXO10000G6-O','CID':'TXO','ContractMonth':'202607','StrikePrice':'10000','CP':'C'}]
    assert resolve_option_identity(rows,cid='TXO',month='202607',strike='10000',option_type='C',session_suffix='-O')['status']=='resolved_from_bootstrap_row'
    assert resolve_option_identity(rows,cid='TXO',month='202607F2',strike='10000',option_type='C',session_suffix='-O')['status']=='no_symbol_match'
    rows.append({'SymbolID':'TXO10000G6-O','CID':'TXO','ContractMonth':'202607','StrikePrice':'10000','CP':'C'})
    assert resolve_option_identity(rows,cid='TXO',month='202607',strike='10000',option_type='C',session_suffix='-O')['status']=='multiple_symbol_matches'
