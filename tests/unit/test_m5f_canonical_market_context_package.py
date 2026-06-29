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

def test_write_package_uses_lf_bytes_for_hash_bound_artifacts(tmp_path):
 out=tmp_path/'pkg'; write_package(out, build_package()); validate_package(out)
 for p in out.iterdir():
  if p.suffix in {'.json', '.md'}:
   assert b'\r\n' not in p.read_bytes()

def test_manifest_tampering_rejected(tmp_path):
 out=tmp_path/'pkg'; shutil.copytree(PKG,out); data=json.loads((out/'canonical_market_context.json').read_text()); data['symbols'][0]['price_like_value']=1; (out/'canonical_market_context.json').write_text(json.dumps(data));
 with pytest.raises(ValueError): validate_package(out)
def test_extra_file_rejected(tmp_path):
 out=tmp_path/'pkg'; shutil.copytree(PKG,out); (out/'extra.txt').write_text('x')
 with pytest.raises(ValueError): validate_package(out)
def test_builder_rejects_forbidden_output():
 with pytest.raises(ValueError): write_package(Path('research/generated/m5f_bad'), build_package())


def test_extra_directory_rejected(tmp_path):
    out=tmp_path/'pkg'; shutil.copytree(PKG,out); (out/'unexpected_dir').mkdir()
    with pytest.raises(ValueError, match='unexpected package directory'):
        validate_package(out)


def test_nested_unexpected_file_rejected(tmp_path):
    out=tmp_path/'pkg'; shutil.copytree(PKG,out); nested=out/'unexpected_dir'; nested.mkdir(); (nested/'extra.json').write_text('{}')
    with pytest.raises(ValueError, match='unexpected package directory'):
        validate_package(out)


def test_extra_non_json_file_rejected(tmp_path):
    out=tmp_path/'pkg'; shutil.copytree(PKG,out); (out/'extra.bin').write_bytes(b'x')
    with pytest.raises(ValueError, match='exact file set mismatch'):
        validate_package(out)


def test_committed_package_still_validates():
    assert validate_package(PKG)['status']=='passed'


def test_hash_bound_artifacts_are_lf_pinned_by_gitattributes():
    attrs = Path('.gitattributes').read_text(encoding='utf-8')
    for pattern in [
        'research/staging/m5f/**/*.json text eol=lf',
        'research/staging/m5f/**/*.md text eol=lf',
        'research/staging/m5d/**/*.json text eol=lf',
        'research/staging/m5c/**/*.json text eol=lf',
    ]:
        assert pattern in attrs


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

def test_recursive_forbidden_symbol_field_rejected(tmp_path):
    out=tmp_path/'pkg'; shutil.copytree(PKG,out)
    data=json.loads((out/'canonical_market_context.json').read_text())
    data['symbols'][0]['target_price']=999
    (out/'canonical_market_context.json').write_text(json.dumps(data, ensure_ascii=False, indent=2))
    manifest=json.loads((out/'sha256_manifest.json').read_text())
    import hashlib
    manifest['files']['canonical_market_context.json']=hashlib.sha256((out/'canonical_market_context.json').read_bytes()).hexdigest()
    (out/'sha256_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    with pytest.raises(ValueError, match='forbidden'):
        validate_package(out)


def _write_candidate_fixture(tmp_path, mutate):
    src=Path('research/staging/m5d/m5d_frontend_publication_candidate_01')
    out=tmp_path/f'candidate_{len(list(tmp_path.iterdir()))}'; shutil.copytree(src,out)
    data=json.loads((out/'market-context.json').read_text())
    mutate(data)
    (out/'market-context.json').write_bytes((json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)+'\n').encode('utf-8'))
    manifest=json.loads((out/'sha256_manifest.json').read_text())
    import hashlib
    manifest['files']['market-context.json']=hashlib.sha256((out/'market-context.json').read_bytes()).hexdigest()
    (out/'sha256_manifest.json').write_bytes((json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)+'\n').encode('utf-8'))
    return out/'market-context.json'


def test_candidate_source_must_match_source_binding(tmp_path):
    candidate=_write_candidate_fixture(tmp_path, lambda data: [row.update({'source_id':'Yahoo_Finance'}) for row in data['symbols']])
    with pytest.raises(ValueError, match='source binding'):
        build_package(candidate)


def test_candidate_targets_must_match_source_binding(tmp_path):
    def mutate(data):
        row=dict(data['symbols'][0]); row['symbol']='9999'; data['symbols'].append(row)
    candidate=_write_candidate_fixture(tmp_path, mutate)
    with pytest.raises(ValueError, match='source binding targets|bounded target'):
        build_package(candidate)


def test_full_market_candidate_rejected(tmp_path):
    candidate=_write_candidate_fixture(tmp_path, lambda data: data.update({'target_universe_mode':'full_market'}))
    with pytest.raises(ValueError, match='full-market'):
        build_package(candidate)


def test_symbol_type_validation_rejects_bool_nan_and_bad_lists(tmp_path):
    candidate=_write_candidate_fixture(tmp_path, lambda data: data['symbols'][0].update({'price_like_value': True}))
    with pytest.raises(ValueError, match='finite number'):
        build_package(candidate)
    candidate=_write_candidate_fixture(tmp_path, lambda data: data['symbols'][0].update({'display_caveats': [{'bad':'shape'}]}))
    with pytest.raises(ValueError, match='list of non-empty strings'):
        build_package(candidate)
