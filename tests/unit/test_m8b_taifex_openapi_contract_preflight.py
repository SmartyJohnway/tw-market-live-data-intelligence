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
    assert {'taifex_openapi_daily_market_report_fut_v1','taifex_openapi_daily_market_report_opt_v1','taifex_openapi_final_settlement_price_v1'} <= ids
    assert selected('taifex_openapi_daily_market_report_fut_v1')['readiness'] in {'go','conditional_go','blocked'}
    assert selected('taifex_openapi_daily_market_report_opt_v1')['readiness'] in {'go','conditional_go','blocked'}

def test_field_mapping_columns_and_identity_fields():
    rows=mapping(); assert rows
    required='source_id endpoint_contract_id instrument_scope source_field normalized_field data_type unit required_for_identity required_for_core_context AI_context_eligible evidence_status conversion_rule validation_rule partial_row_policy caveats'.split()
    assert set(required) <= set(rows[0])
    ident={(r['endpoint_contract_id'],r['source_field']) for r in rows if r['required_for_identity']=='true'}
    assert ('taifex_openapi_daily_market_report_fut_v1','Contract') in ident
    assert ('taifex_openapi_daily_market_report_fut_v1','ContractMonth(Week)') in ident
    assert ('taifex_openapi_daily_market_report_opt_v1','StrikePrice') in ident
    assert ('taifex_openapi_daily_market_report_opt_v1','CallPut') in ident

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
    row=load(FIX/'taifex_options_normal_rows.json')[0]
    assert int(row['Volume']) == 0 and int(row['OpenInterest']) == 0
    assert 'valid_zero_trade_contract' in doc(CUR)

def test_currentness_and_session_contract():
    text=doc(CUR)
    for s in ['current_official_derivatives_eod','matches_expected_latest_trade_date_after_emergency_closure','delayed_one_trading_day','stale_official_derivatives_eod','unresolved_date_mismatch','session_semantics_unresolved']:
        assert s in text
    assert 'retrieved_at_utc` is fetch time only' in text
    assert 'Weekend latest-prior-date behavior is acceptable' in text
    assert 'do not force TAIFEX to match TWSE/TPEx' in text
    assert 'session to `unknown`' in text

def test_no_raw_payload_artifact_and_boundaries():
    for p in Path('research/probe_runs/m8b_taifex_openapi_derivatives_eod_preflight').glob('*.json'):
        data=load(p); blob=json.dumps(data,ensure_ascii=False)
        assert 'representative_compact_rows' in blob
        assert len(blob) < 80000
    forbidden_dirs=[Path('frontend'),Path('server')]
    # preflight-only boundary is documented and no M8B production script exists yet
    assert not Path('scripts/m8b_taifex_openapi_futures_adapter.py').exists()
    assert not Path('scripts/m8b_taifex_openapi_execution.py').exists()
    acc=doc('docs/protocol/M8B_TAIFEX_OPENAPI_OFFICIAL_DERIVATIVES_EOD_PREFLIGHT_ACCEPTANCE.md')
    for word in ['No production adapter','scheduler','polling','startup fetch','DB write','TAIFEX_MIS','Yahoo','FinMind','recommendation']:
        assert word in acc
