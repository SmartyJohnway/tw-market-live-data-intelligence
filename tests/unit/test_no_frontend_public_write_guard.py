import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))

def test_no_frontend_public_changed_in_diff():
    import subprocess
    out=subprocess.check_output(['git','diff','--name-only','origin/main...HEAD'],cwd=ROOT,text=True)
    assert not any(x.startswith('frontend/public/') for x in out.splitlines())
def test_builder_default_not_frontend_public():
    text=(ROOT/'scripts/build_frontend_readonly_context_package.py').read_text().lower(); assert 'frontend/public' not in text
def test_local_preview_outside_public(): assert (ROOT/'frontend/readonly-preview').exists()
