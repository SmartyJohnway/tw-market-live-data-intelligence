from scripts.m8c_taifex_mis_probe_common import identity_key, resolve_option_identity, resolve_option_identity_exact

def test_product_cid_symbol_distinct_and_sessions_do_not_collide():
    assert 'TX'!='TXF'!='TXFG6-F'
    assert identity_key({'runtime_symbol_id':'TXFG6-F','session':'regular','market_type':'0'}) != identity_key({'runtime_symbol_id':'TXFG6-M','session':'after_hours','market_type':'1'})

def test_deprecated_substring_resolver_fails_closed():
    rows=[{'SymbolID':'TXO10000G6-O','CID':'TXO','ContractMonth':'202607','StrikePrice':'10000','CP':'C'}]
    assert resolve_option_identity(rows,cid='TXO',month='202607',strike='10000',option_type='C',session_suffix='-O')['status']=='deprecated_substring_resolver_not_allowed'

def test_exact_option_identity_does_not_use_substrings():
    rows=[{'SymbolID':'TXO10000G6-O','CID':'TXO','ExpireMonth':'202607','StrikePrice':'10000.0','CP':'C'}, {'SymbolID':'TXO210000G6-O','CID':'TXO','ExpireMonth':'202607','StrikePrice':'210000','CP':'C'}]
    assert resolve_option_identity_exact(rows,cid='TXO',month='202607',strike='10000.00',option_type='CALL',session_suffix='-O')['runtime_symbol_id']=='TXO10000G6-O'
    assert resolve_option_identity_exact(rows,cid='TXO',month='202607',strike='10000',option_type='P',session_suffix='-O')['status']=='no_symbol_match'

def test_exact_option_identity_missing_and_ambiguous_fail_closed():
    missing=[{'SymbolID':'TXO10000G6-O','ExpireMonth':'202607','StrikePrice':'10000','CP':'C'}]
    assert resolve_option_identity_exact(missing,cid='TXO',month='202607',strike='10000',option_type='C',session_suffix='-O')['status']=='no_symbol_match'
    dup=[{'SymbolID':'TXO10000G6-O','CID':'TXO','ExpireMonth':'202607','StrikePrice':'10000','CP':'C'}, {'SymbolID':'TXO10000G6-O','CID':'TXO','ExpireMonth':'202607','StrikePrice':'10000.0','CP':'CALL'}]
    assert resolve_option_identity_exact(dup,cid='TXO',month='202607',strike='10000',option_type='C',session_suffix='-O')['status']=='multiple_symbol_matches'
    assert resolve_option_identity_exact(dup,cid='TXO',month='202607',strike='bad',option_type='C',session_suffix='-O')['status']=='ambiguous_option_identity'
from scripts.m8c_taifex_mis_probe_common import resolve_option_identity_from_scoped_rows

def test_scoped_option_identity_uses_observed_row_shape():
    rows=[{'SymbolID':'TXV40100G6-O','StrikePrice':'40100','CP':'C','DispEName':'TXV'}, {'SymbolID':'TXV40100G6-N','StrikePrice':'40100','CP':'C'}]
    scope={'CID':'TXO','ExpireMonth':'202607F2','MarketType':'0','SymbolType':'O'}
    out=resolve_option_identity_from_scoped_rows(rows,scope=scope,strike='40100.0',option_type='CALL',session_suffix='-O')
    assert out['status']=='resolved_from_scoped_bootstrap_row'
    assert out['runtime_symbol_id']=='TXV40100G6-O'
    assert out['scope']['CID']=='TXO'

def test_scoped_option_identity_requires_scope_provenance():
    rows=[{'SymbolID':'TXV40100G6-O','StrikePrice':'40100','CP':'C'}]
    assert resolve_option_identity_from_scoped_rows(rows,scope={'CID':'TXO','MarketType':'0','SymbolType':'O'},strike='40100',option_type='C',session_suffix='-O')['status']=='scope_provenance_missing'
    assert resolve_option_identity_from_scoped_rows(rows,scope={'CID':'TXO','ExpireMonth':'202607F2','MarketType':'0','SymbolType':'F'},strike='40100',option_type='C',session_suffix='-O')['status']=='scope_provenance_inconsistent'
