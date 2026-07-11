from scripts.m8a_tpex_official_eod_adapter import classify_instrument
from scripts.m8a_twse_official_eod_adapter import parse_twse_official_eod_rows
from scripts.m8a_official_eod_instrument_classifier import classify_official_eod_instrument, build_security_master_lookup
from scripts.m8a_official_eod_observation import observation_to_context_observation, create_observation

def test_security_master_primary_classifier_no_symbol_length_heuristic():
    assert classify_instrument("tpex_otc","006201") ["instrument_type"] == "etf"
    assert classify_official_eod_instrument("listed","0050")["instrument_type"] == "etf"
    assert classify_official_eod_instrument("listed","2330")["instrument_type"] == "equity"
    assert classify_official_eod_instrument("listed","00929")["instrument_type"] == "etf"
    assert classify_official_eod_instrument("listed","00400A")["instrument_type"] == "etf"
    un=classify_instrument("tpex_otc","1234")
    assert un["instrument_type"] == "unknown" and un["classification_status"] == "unclassified"

def test_unclassified_context_fail_closed():
    obs=create_observation(source_id="TPEX_OPENAPI",endpoint_contract_id="x",market="tpex_otc",symbol="1234",name="x",instrument_type="unknown",trade_date="2026-07-09")
    ctx=observation_to_context_observation(obs)
    assert ctx["safe_fields"] == {}
    assert "unclassified" in " ".join(ctx["caveats"])


def test_twse_parser_uses_classifier_for_0050_not_equity():
    rows=[{"Date":"1150709","Code":"0050","Name":"元大台灣50","TradeVolume":"100","TradeValue":"10000","OpeningPrice":"100","HighestPrice":"101","LowestPrice":"99","ClosingPrice":"100","Change":"0","Transaction":"10"},{"Date":"1150709","Code":"2330","Name":"台積電","TradeVolume":"100","TradeValue":"10000","OpeningPrice":"100","HighestPrice":"101","LowestPrice":"99","ClosingPrice":"100","Change":"0","Transaction":"10"}]
    r=parse_twse_official_eod_rows(rows, requested_symbols=['0050','2330'])
    types={o['symbol']:o['instrument_type'] for o in r['observations']}
    assert types['0050']=='etf'
    assert types['2330']=='equity'

def test_tpex_production_classification_loads_repository_security_master():
    lookup=build_security_master_lookup()
    assert lookup[('tpex_otc','8069')]['instrument_type']=='equity'
    assert classify_official_eod_instrument('tpex_otc','006201')['instrument_type']=='etf'

def test_bounded_seed_only_status_when_canonical_master_unavailable():
    result=classify_official_eod_instrument('listed','0050')
    assert result['coverage_mode'] in {'bounded_seed_only','canonical_security_master'}
    if result['coverage_mode']=='bounded_seed_only':
        assert result['production_classification_completeness']=='incomplete'
        assert result['artifact_path']=='config/m8a_official_eod_security_master.json'
