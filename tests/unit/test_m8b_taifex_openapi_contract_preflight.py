import csv, json, re
from decimal import Decimal, InvalidOperation
from pathlib import Path

REG=Path('docs/data_capabilities/m8b_taifex_openapi_endpoint_contract_registry.json')
MAP=Path('docs/data_capabilities/m8b_taifex_openapi_field_mapping.csv')
SCHEMA=Path('docs/protocol/M8B_TAIFEX_DERIVATIVES_NORMALIZED_OBSERVATION_SCHEMA.md')
CUR=Path('docs/protocol/M8B_TAIFEX_DERIVATIVES_CURRENTNESS_AND_SESSION_CONTRACT.md')
FIX=Path('tests/fixtures/m8b_taifex_openapi')

def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def registry(): return load(REG)
def mapping(): return list(csv.DictReader(MAP.open(encoding='utf-8')))
def doc(p): return Path(p).read_text(encoding='utf-8')
def selected(cid): return next(e for e in registry()['selected_endpoints'] if e['endpoint_contract_id']==cid)

def identity_key(row, opt=False):
    if not row.get('Contract') or not row.get('ContractMonth(Week)'): raise ValueError('identity_parse_failure')
    if not re.match(r'^\d{6}([A-Z0-9]+)?$', row['ContractMonth(Week)']): raise ValueError('identity_parse_failure')
    if opt and (not row.get('StrikePrice') or not row.get('CallPut')): raise ValueError('identity_parse_failure')
    return tuple([row.get('Date'), row.get('Contract'), row.get('ContractMonth(Week)'), row.get('StrikePrice'), row.get('CallPut'), row.get('TradingSession','unknown')])

def decimal_ok(v, signed=False):
    if v in (None,'','-','--','---'): return True
    d=Decimal(str(v).replace(',','').replace('%',''))
    return signed or d >= 0

def test_registry_schema_and_selected_endpoints():
    r=registry(); assert r['schema_version']=='m8b_taifex_openapi_endpoint_contract_registry.v1'
    ids={e['endpoint_contract_id'] for e in r['selected_endpoints']}
    assert {'taifex_openapi_daily_market_report_fut_v1','taifex_openapi_daily_market_report_opt_v1','taifex_openapi_final_settlement_price_v1','taifex_openapi_large_trader_oi_futures_v1','taifex_openapi_large_trader_oi_options_v1'} <= ids
    assert selected('taifex_openapi_daily_market_report_fut_v1')['readiness'] in {'go','conditional_go','blocked'}
    assert selected('taifex_openapi_daily_market_report_opt_v1')['readiness'] in {'go','conditional_go','blocked'}
    assert selected('taifex_openapi_large_trader_oi_futures_v1')['implementation_recommendation'] == 'implement_in_M8B_01'
    assert selected('taifex_openapi_large_trader_oi_options_v1')['context_type'] == 'official_derivatives_large_trader_open_interest_reference'

def test_field_mapping_columns_and_identity_fields():
    rows=mapping(); assert rows
    required='source_id endpoint_contract_id instrument_scope source_field normalized_field data_type unit required_for_identity required_for_core_context AI_context_eligible evidence_status conversion_rule validation_rule partial_row_policy caveats'.split()
    assert set(required) <= set(rows[0])
    ident={(r['endpoint_contract_id'],r['source_field']) for r in rows if r['required_for_identity']=='true'}
    assert ('taifex_openapi_daily_market_report_fut_v1','Contract') in ident
    assert ('taifex_openapi_daily_market_report_fut_v1','ContractMonth(Week)') in ident
    assert ('taifex_openapi_daily_market_report_opt_v1','StrikePrice') in ident
    assert ('taifex_openapi_daily_market_report_opt_v1','CallPut') in ident
    assert ('taifex_openapi_large_trader_oi_futures_v1','TypeOfTraders') in ident
    assert ('taifex_openapi_large_trader_oi_options_v1','CallPut') in ident

def test_identity_contract_rejects_symbol_only_and_bad_rows():
    assert 'Symbol-only identity is invalid' in doc(SCHEMA)
    assert identity_key(load(FIX/'taifex_futures_normal_rows.json')[0])
    assert identity_key(load(FIX/'taifex_options_normal_rows.json')[0], opt=True)
    for f,opt in [('taifex_futures_invalid_contract_month.json',False),('taifex_options_missing_strike_or_callput.json',True)]:
        try: identity_key(load(FIX/f)[0], opt=opt)
        except ValueError as e: assert str(e)=='identity_parse_failure'
        else: raise AssertionError('bad identity accepted')
    assert 'Duplicate derivative contract identity fails closed' in doc(SCHEMA)

def test_duplicate_identity_and_mixed_date_fixtures():
    for f,opt in [('taifex_futures_duplicate_identity.json',False),('taifex_options_duplicate_identity.json',True)]:
        keys=[identity_key(r,opt) for r in load(FIX/f)]
        assert len(keys) != len(set(keys))
    assert len({r['Date'] for r in load(FIX/'taifex_futures_mixed_date.json')}) > 1
    assert 'date_mismatch' in doc(CUR)

def test_price_semantics_decimal_and_no_float_policy():
    text=doc(SCHEMA)
    assert 'settlement != close' in text and 'reference != last' in text and 'never floats' in text
    fields={r['source_field']:r['normalized_field'] for r in mapping() if r['endpoint_contract_id']=='taifex_openapi_daily_market_report_fut_v1'}
    assert fields['SettlementPrice']=='price.settlement' and fields['Last']=='price.last'
    opt_fields={r['source_field']:r['normalized_field'] for r in mapping() if r['endpoint_contract_id']=='taifex_openapi_daily_market_report_opt_v1'}
    assert opt_fields['Close']=='price.close' and opt_fields['SettlementPrice']=='price.settlement'
    assert decimal_ok('45648') and decimal_ok('-1', signed=True)
    try: decimal_ok('-1')
    except Exception: raise
    assert decimal_ok('-1') is False
    try: decimal_ok('abc')
    except InvalidOperation: pass
    else: raise AssertionError('malformed numeric accepted')

def test_activity_open_interest_and_zero_volume_valid():
    rows=mapping(); n={r['source_field']:r['normalized_field'] for r in rows}
    assert n['Volume']=='activity.volume'; assert n['OpenInterest']=='open_interest.open_interest'
    rows=mapping()
    for source_field in ['Volume','OpenInterest','Top5Buy','Top5Sell','Top10Buy','Top10Sell','OIOfMarket']:
        typed=[r for r in rows if r['source_field']==source_field]
        assert typed
        assert all(r['data_type']=='integer' for r in typed)
        assert all('non-negative integer' in r['validation_rule'] for r in typed)
    row=load(FIX/'taifex_options_normal_rows.json')[0]
    assert int(row['Volume']) == 0 and int(row['OpenInterest']) == 0
    assert 'valid_zero_trade_contract' in doc(CUR)


def test_derivatives_quotation_units_not_hardcoded_twd():
    rows=mapping()
    tx_settlement=[r for r in rows if r['endpoint_contract_id']=='taifex_openapi_daily_market_report_fut_v1' and r['source_field']=='SettlementPrice'][0]
    txo_strike=[r for r in rows if r['endpoint_contract_id']=='taifex_openapi_daily_market_report_opt_v1' and r['source_field']=='StrikePrice'][0]
    assert tx_settlement['unit'] != 'TWD'
    assert txo_strike['unit'] != 'TWD'
    assert tx_settlement['unit'] == 'product_specific_quote_unit'
    assert txo_strike['unit'] == 'product_specific_quote_unit'
    schema = doc(SCHEMA)
    assert 'settlement_currency' in schema and 'quotation_unit' in schema and 'contract_multiplier' in schema
    assert 'TX, MTX, and TXO price/strike/settlement values must not be projected as TWD prices' in schema

def test_put_call_ratio_mapping_complete_and_percent_semantics():
    rows=[r for r in mapping() if r['endpoint_contract_id']=='taifex_openapi_put_call_ratio_v1']
    fields={r['source_field']:r for r in rows}
    assert {'Date','PutVolume','CallVolume','PutCallVolumeRatio%','PutOI','CallOI','PutCallOIRatio%'} <= set(fields)
    for f in ['PutVolume','CallVolume','PutOI','CallOI']:
        assert fields[f]['data_type']=='integer'
        assert 'non-negative integer' in fields[f]['validation_rule']
    assert fields['PutCallVolumeRatio%']['unit']=='percent'
    assert '100.89 means 100.89%, not 1.0089' in fields['PutCallVolumeRatio%']['validation_rule']
    assert 'no bullish/bearish derived output' in fields['PutCallOIRatio%']['caveats']

def test_block_trade_mapping_identity_rules():
    rows=[r for r in mapping() if r['endpoint_contract_id']=='taifex_openapi_block_trade_v1']
    fields={r['source_field']:r for r in rows}
    assert {'Date','Contract','ContractMonth(Week)','StrikePrice','CallPut','Volume','HighestPrice','LowestPrice','TradingSession'} <= set(fields)
    assert 'futures not_applicable' in fields['StrikePrice']['caveats']
    assert 'options require valid CallPut' in fields['CallPut']['caveats']
    assert fields['Volume']['data_type']=='integer'
    assert fields['HighestPrice']['unit']=='product_specific_quote_unit'

def test_putcall_and_blocktrade_registry_common_shape_and_aggregate_identity():
    candidates={c['endpoint_contract_id']:c for c in registry()['candidate_endpoints']}
    required={'source_id','method','evidence_status','timing_class','instrument_scope','network_scope','retained_scope_required','date_parameter_contract','product_parameter_contract','identity_fields','trade_date_fields','price_fields','activity_fields','open_interest_fields','session_fields','caveats'}
    for cid in ['taifex_openapi_put_call_ratio_v1','taifex_openapi_block_trade_v1']:
        assert required <= set(candidates[cid])
        assert candidates[cid]['source_id']=='TAIFEX_OPENAPI'
        assert candidates[cid]['method']=='GET'
    assert candidates['taifex_openapi_put_call_ratio_v1']['identity_fields']==[]
    assert candidates['taifex_openapi_put_call_ratio_v1']['retained_scope_required']=='aggregate_endpoint_defined_no_contract_identity'
    assert 'Aggregate statistical reference' in ' '.join(candidates['taifex_openapi_put_call_ratio_v1']['caveats'])

def test_large_trader_not_labeled_three_institutional_investor_data():
    text = REG.read_text(encoding='utf-8') + MAP.read_text(encoding='utf-8') + doc('docs/protocol/M8B_01_TAIFEX_OPENAPI_IMPLEMENTATION_BLUEPRINT.md')
    banned=['three-institutional','institutional/large-trader','foreign investor net position','dealer net position','investment trust net position']
    assert not any(term in text for term in banned)
    assert 'large trader open-interest concentration' in text

def test_currentness_and_session_contract():
    text=doc(CUR)
    for s in ['current_official_derivatives_eod','matches_expected_latest_trade_date_after_emergency_closure','delayed_one_trading_day','stale_official_derivatives_eod','unresolved_date_mismatch','session_semantics_unresolved']:
        assert s in text
    assert 'retrieved_at_utc` is fetch time only' in text
    assert 'Weekend latest-prior-date behavior is acceptable' in text
    assert 'do not force TAIFEX to match TWSE/TPEx' in text
    assert 'session to `unknown`' in text


def test_final_settlement_contract_has_no_daily_activity_or_session():
    ep=selected('taifex_openapi_final_settlement_price_v1')
    assert ep['trade_date_fields']==['TheFinalSettlementDay']
    assert ep['date_parameter_contract']['source_trade_date_field']=='TheFinalSettlementDay'
    assert ep['activity_fields']==[]
    assert ep['open_interest_fields']==[]
    assert ep['session_fields']==[]
    assert 'Volume' not in ep['field_contract'] and 'OpenInterest' not in ep['field_contract'] and 'TradingSession' not in ep['field_contract']
    assert 'expiry final settlement only' in ' '.join(ep['caveats'])

def test_discovered_reference_endpoints_and_blueprint_matrix():
    candidates={c['endpoint_contract_id']:c for c in registry()['candidate_endpoints']}
    assert candidates['taifex_openapi_put_call_ratio_v1']['implementation_recommendation']=='implement_in_M8B_01'
    assert candidates['taifex_openapi_block_trade_v1']['implementation_recommendation']=='implement_in_M8B_01'
    assert candidates['taifex_openapi_contract_adjustment_v1']['implementation_recommendation']=='deferred_with_specific_reason'
    assert candidates['taifex_openapi_trading_calendar']['implementation_recommendation']=='unresolved'
    bp=doc('docs/protocol/M8B_01_TAIFEX_OPENAPI_IMPLEMENTATION_BLUEPRINT.md')
    for endpoint in ['DailyMarketReportFut','DailyMarketReportOpt','FinalSettlementPrice','OpenInterestOfLargeTradersFutures','OpenInterestOfLargeTradersOptions','PutCallRatio','BlockTrade','ContractAdj','Trading calendar']:
        assert endpoint in bp
    assert 'no bullish/bearish signal or recommendation' in bp

def test_no_raw_payload_artifact_and_boundaries():
    for p in Path('research/probe_runs/m8b_taifex_openapi_derivatives_eod_preflight').glob('*.json'):
        data=load(p); blob=json.dumps(data,ensure_ascii=False)
        assert 'representative_compact_rows' in blob
        assert len(blob) < 80000
    forbidden_dirs=[Path('frontend'),Path('server')]
    # M8B-01 may add controlled production adapters; preflight artifacts still must not retain raw payloads or add UI/server surfaces.
    assert Path('scripts/m8b_taifex_openapi_futures_adapter.py').exists()
    assert Path('scripts/m8b_taifex_openapi_execution.py').exists()
    acc=doc('docs/protocol/M8B_TAIFEX_OPENAPI_OFFICIAL_DERIVATIVES_EOD_PREFLIGHT_ACCEPTANCE.md')
    for word in ['No production adapter','scheduler','polling','startup fetch','DB write','TAIFEX_MIS','Yahoo','FinMind','recommendation','bullish/bearish scoring','raw payload retention']:
        assert word in acc
