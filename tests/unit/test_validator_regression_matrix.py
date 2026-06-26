import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))

from scripts.controlled_refresh_staging_validator import validate_controlled_refresh_staging_payload
def base(): return json.loads((ROOT/'tests/fixtures/staging_payloads/valid_single_source_twse_mis.json').read_text())
def test_source_id_allowlist_and_safe_bounded_universe():
    p=base(); assert validate_controlled_refresh_staging_payload(p)==[]; p['source_runs'][0]['source_id']='Bad'; assert validate_controlled_refresh_staging_payload(p)
def test_forbidden_keys_recursively_and_flags():
    p=base(); p['source_runs'][0]['normalized_sample_preview']['recommendation']='x'; assert validate_controlled_refresh_staging_payload(p)
def test_target_scope_mode_case_insensitive_full_market_blocking():
    for k in ['scope','mode']:
        p=base(); p['target_universe'][k]='Full_Market'; assert validate_controlled_refresh_staging_payload(p)
def test_twse_mis_unofficial_risk_aliases():
    for alias in ['unofficial_source_risk','unofficial_endpoint','unofficial_frontend_endpoint']:
        p=base(); p['source_runs'][0]['source_risk_flags']=[alias]; assert validate_controlled_refresh_staging_payload(p)==[]
