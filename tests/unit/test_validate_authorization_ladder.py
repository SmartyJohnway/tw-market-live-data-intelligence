from datetime import datetime, timezone
from pathlib import Path
import json, subprocess, sys
ROOT=Path(__file__).resolve().parents[2]
from scripts.validate_authorization_ladder import validate_authorization_ladder, validate_authorization_token

def valid_token():
    return {
        'token_id':'fixture-token',
        'authorization_level':'fixture_replay',
        'authorized_by':'operator',
        'authorized_at':'2026-06-26T00:00:00Z',
        'expires_at':'2099-01-01T00:00:00Z',
        'allowed_actions':['local_validation','fixture_replay'],
        'forbidden_actions':['production_refresh','live_probe','frontend_publication','trading_signal','full_market_scan','broker_auth'],
        'allowed_sources':['Fixture_Synthetic'],
        'allowed_target_universe':{'mode':'fixture','full_market_scan':False},
        'output_path_policy':'safe_tmp_only',
        'no_trading_signal':True,
        'no_realtime_guarantee':True,
        'no_production_write':True,
    }

def test_ladder_blocks_elevation(): assert validate_authorization_ladder({'live_probe_authorized':True})
def test_ladder_local_ok(): assert validate_authorization_ladder({}) == []
def test_valid_authorization_token_passes_schema_and_policy(): assert validate_authorization_token(valid_token(), ROOT/'docs/authorization/authorization_token_schema.json') == []
def test_token_granting_forbidden_action_fails():
    token=valid_token(); token['allowed_actions'].append('production_refresh')
    errors=validate_authorization_token(token, ROOT/'docs/authorization/authorization_token_schema.json')
    assert any(e['code']=='token_grants_forbidden_actions' for e in errors)
def test_expired_or_full_market_token_fails():
    token=valid_token(); token['expires_at']='2000-01-01T00:00:00Z'; token['allowed_target_universe']['full_market_scan']=True
    codes={e['code'] for e in validate_authorization_token(token, ROOT/'docs/authorization/authorization_token_schema.json')}
    assert {'authorization_token_expired','schema_const_mismatch','token_full_market_scan_forbidden'} & codes
