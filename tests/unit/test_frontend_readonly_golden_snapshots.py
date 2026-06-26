import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))

from scripts.build_frontend_readonly_context_package import build_frontend_readonly_context_package, REQUIRED_CAVEATS
def test_builder_output_matches_golden():
    pairs=[('valid_single_source_twse_mis.json','golden_single_source_twse_mis.json'),('valid_multi_source_mixed.json','golden_multi_source_mixed.json')]
    for s,g in pairs:
        assert build_frontend_readonly_context_package(json.loads((ROOT/'tests/fixtures/staging_payloads'/s).read_text())) == json.loads((ROOT/'tests/fixtures/frontend_readonly_packages'/g).read_text())
def test_caveats_and_forbidden_flags():
    for p in (ROOT/'tests/fixtures/frontend_readonly_packages').glob('golden_*.json'):
        data=json.loads(p.read_text()); assert all(c in data['global_caveats'] for c in REQUIRED_CAVEATS)
        assert data['trading_signal'] is False and data['realtime_guaranteed'] is False and data['production_current_state'] is False
