import json, shutil, subprocess, sys
from pathlib import Path
import pytest
from scripts.validate_m5f_canonical_market_context_package import validate_package
from scripts.build_m5f_canonical_market_context_package import build_package, write_package
PKG=Path('research/staging/m5f/m5f_canonical_market_context_01')
def test_validate_package_exact_values():
 r=validate_package(PKG); assert r['symbols']==['0050','00929','2330']; assert r['source']=='TWSE_OpenAPI'; assert r['source_date']=='2026-06-26'
def test_deterministic_rebuild(tmp_path):
 out=tmp_path/'pkg'; write_package(out, build_package());
 for p in PKG.iterdir(): assert p.read_bytes()==(out/p.name).read_bytes()
def test_manifest_tampering_rejected(tmp_path):
 out=tmp_path/'pkg'; shutil.copytree(PKG,out); data=json.loads((out/'canonical_market_context.json').read_text()); data['symbols'][0]['price_like_value']=1; (out/'canonical_market_context.json').write_text(json.dumps(data));
 with pytest.raises(ValueError): validate_package(out)
def test_extra_file_rejected(tmp_path):
 out=tmp_path/'pkg'; shutil.copytree(PKG,out); (out/'extra.txt').write_text('x')
 with pytest.raises(ValueError): validate_package(out)
def test_builder_rejects_forbidden_output():
 with pytest.raises(ValueError): write_package(Path('research/generated/m5f_bad'), build_package())


def test_builder_rejects_repo_directories():
    import pytest
    from scripts.build_m5f_canonical_market_context_package import build_package, write_package
    for bad in [Path('scripts'), Path('server'), Path('docs')]:
        with pytest.raises(ValueError):
            write_package(bad, build_package())

def test_write_package_rolls_back_on_final_replace_failure(tmp_path, monkeypatch):
    import os, json
    from scripts.build_m5f_canonical_market_context_package import build_package, write_package
    out = tmp_path / 'pkg'
    write_package(out, build_package())
    original = (out / 'canonical_market_context.json').read_bytes()
    real_replace = os.replace
    calls = {'count': 0}
    def flaky_replace(src, dst):
        if str(dst) == str(out):
            calls['count'] += 1
            if calls['count'] == 1:
                raise OSError('injected final replace failure')
        return real_replace(src, dst)
    monkeypatch.setattr(os, 'replace', flaky_replace)
    try:
        write_package(out, build_package())
    except OSError:
        pass
    assert (out / 'canonical_market_context.json').read_bytes() == original


def test_cli_check_only_and_write_package_mutually_exclusive():
    import subprocess, sys
    cp = subprocess.run([sys.executable, 'scripts/build_m5f_canonical_market_context_package.py', '--check-only', '--write-package'], capture_output=True, text=True)
    assert cp.returncode != 0
    assert 'not allowed with argument' in cp.stderr
