import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))

from scripts.controlled_refresh_staging_validator import validate_controlled_refresh_staging_payload, ALLOWED_SOURCE_IDS
def valid_payloads(): return sorted((ROOT/'tests/fixtures/staging_payloads').glob('valid_*.json'))
def test_all_valid_fixtures_validate():
    for p in valid_payloads(): assert validate_controlled_refresh_staging_payload(json.loads(p.read_text())) == []
def test_allowed_sources_flags_no_trading_realtime_or_production_claims():
    for p in valid_payloads():
        data=json.loads(p.read_text()); assert data['validation']['trading_signal'] is False
        text=p.read_text().lower(); assert 'realtime_guaranteed' not in text and 'production_current_state' not in text
        for r in data['source_runs']: assert r['source_id'] in ALLOWED_SOURCE_IDS
def test_twse_mis_risk_preserved():
    for p in valid_payloads():
        for r in json.loads(p.read_text())['source_runs']:
            if r['source_id']=='TWSE_MIS': assert any('unofficial' in x for x in r['source_risk_flags'])
