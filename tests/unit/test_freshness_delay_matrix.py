import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))

from scripts.controlled_refresh_staging_validator import FRESHNESS, DELAY, validate_controlled_refresh_staging_payload
from scripts.build_frontend_readonly_context_package import build_frontend_readonly_context_package
def test_valid_enum_pairs_pass():
    m=json.loads((ROOT/'tests/fixtures/staging_payloads/freshness_delay_matrix.json').read_text()); assert set(m['freshness_status'])<=FRESHNESS and set(m['delay_status'])<=DELAY
def test_invalid_enum_fails():
    p=json.loads((ROOT/'tests/fixtures/staging_payloads/valid_single_source_twse_mis.json').read_text()); p['source_runs'][0]['freshness_status']='bad'; assert validate_controlled_refresh_staging_payload(p)
def test_live_candidate_not_realtime_guarantee(): assert 'not a realtime guarantee' in (ROOT/'tests/fixtures/staging_payloads/freshness_delay_matrix.json').read_text()
def test_stale_and_delayed_caveats_downstream():
    for f,c in [('valid_stale_payload.json','stale_source_row'),('valid_delayed_payload.json','delayed_source_row')]:
        pkg=build_frontend_readonly_context_package(json.loads((ROOT/'tests/fixtures/staging_payloads'/f).read_text())); assert c in pkg['symbols'][0]['display_caveats']
