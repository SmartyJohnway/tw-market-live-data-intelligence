import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))

def files(): return list((ROOT/'frontend/readonly-preview').glob('*'))
def test_required_frontend_preview_files_exist():
    for f in ['readonlyContextAdapter.js','ReadonlyMarketContextPreview.html','readonlyCaveatBadges.js','sourceAuthorityDisplay.js','readonly-preview.js']: assert (ROOT/'frontend/readonly-preview'/f).exists()
def test_required_wording_exists_and_forbidden_positive_claims_absent():
    text='\n'.join(p.read_text().lower() for p in files())
    for phrase in ['not realtime guaranteed','not a trading signal','not production current state','local preview only','source authority']:
        assert phrase in text
    for phrase in ['target price','recommendation']:
        assert phrase not in text
