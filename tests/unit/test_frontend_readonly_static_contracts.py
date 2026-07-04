import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))

def files(): return list((ROOT/'frontend/readonly-preview').glob('*'))
def test_required_frontend_preview_files_exist():
    for f in ['readonlyContextAdapter.js','ReadonlyMarketContextPreview.html','readonlyCaveatBadges.js','sourceAuthorityDisplay.js','readonly-preview.js']: assert (ROOT/'frontend/readonly-preview'/f).exists()
