import hashlib,json,os,sys
from pathlib import Path
import pytest
from packaging_native.bootstrap.package_integrity import canonical_digest,verify_bundle
from packaging_native.bootstrap.bootstrap import bootstrap
from scripts.build_native_distribution import check_member,inspect_wheels

@pytest.fixture
def bundle(tmp_path):
    (tmp_path/'app').mkdir()
    (tmp_path/'app/x.txt').write_bytes(b'abc')
    m=dict(schema_version=1,product_name='TW-Market',product_version='1.0.0',source_commit='a'*40,source_tree='b'*40,target_os='windows',target_arch='x64',python_requirement='CPython 3.13 x64',package_profile='test',member_count=1,members=[dict(relative_path='app/x.txt',role='application',bytes=3,sha256=hashlib.sha256(b'abc').hexdigest())])
    save(tmp_path,m)
    return tmp_path,m

def save(root,m):
    m['manifest_canonical_sha256']=canonical_digest(m)
    (root/'distribution-manifest.json').write_text(json.dumps(m),encoding='utf-8')

def test_valid_and_runtime(bundle):
    r,m=bundle
    verify_bundle(r)
    (r/'runtime').mkdir(); (r/'runtime/derived').write_text('x')
    verify_bundle(r)

@pytest.mark.parametrize('path',['../x','/x','C:/x','app\\x','app/CON','app/aux.txt','app/COM¹.txt','app/x.','app/x ','app/a:b','app/a?b','app//x','app/./x','runtime/x','distribution-manifest.json'])
def test_unsafe_path(bundle,path):
    r,m=bundle; m['members'][0]['relative_path']=path; save(r,m)
    with pytest.raises(ValueError): verify_bundle(r)

@pytest.mark.parametrize('change',['self','bytes','sha','missing','extra','extra-dir','duplicate','case','count','bool','identity','schema','member-role'])
def test_tamper(bundle,change):
    r,m=bundle
    if change=='self':
        m['product_version']='2'; (r/'distribution-manifest.json').write_text(json.dumps(m))
    elif change in {'bytes','sha'}:
        (r/'app/x.txt').write_bytes(b'xyzq' if change=='bytes' else b'xyz')
    elif change=='missing': (r/'app/x.txt').unlink()
    elif change=='extra': (r/'app/evil.py').write_text('evil')
    elif change=='extra-dir': (r/'.git').mkdir()
    else:
        if change in {'duplicate','case'}:
            m['members'].append(dict(m['members'][0],relative_path='APP/X.TXT' if change=='case' else 'app/x.txt')); m['member_count']=2
        elif change=='count':m['member_count']=2
        elif change=='bool':m['member_count']=True
        elif change=='identity':m['source_commit']='x'
        elif change=='schema':m['schema_version']=True
        elif change=='member-role':m['members'][0]['role']='unknown'
        save(r,m)
    with pytest.raises(ValueError): verify_bundle(r)

@pytest.mark.parametrize('where',['root','manifest','runtime'])
def test_reparse(bundle,tmp_path,where):
    r,m=bundle
    target=r/'app/x.txt'
    link=r/'runtime/link'
    if where=='root': link=r.parent/(r.name+'-link');target=r
    elif where=='manifest':
        target=r/'original.json'; (r/'distribution-manifest.json').rename(target);link=r/'distribution-manifest.json'
    else: (r/'runtime').mkdir()
    try:link.symlink_to(target,target_is_directory=where=='root')
    except OSError:pytest.skip('host symlink privilege unavailable')
    with pytest.raises(ValueError): verify_bundle(link if where=='root' else r)

def test_bootstrap_missing_resources_before_write(bundle):
    r,m=bundle
    with pytest.raises(RuntimeError,match='resources missing'): bootstrap(r)
    assert not (r/'runtime').exists()

@pytest.mark.parametrize('path',['app/data/x','app/tests/test.py','.git/config','app/.env','app/installation.json'])
def test_exclusion(path):
    with pytest.raises(ValueError):check_member(path,b'plain')

def test_host_leakage():
    with pytest.raises(ValueError):check_member('app/x.txt',('C:'+chr(92)+'Users'+chr(92)+'weitang').encode())

def test_allowlist_exact_and_resources():
    root=Path(__file__).parents[2]
    p=json.loads((root/'packaging_native/resource-policy.json').read_text())
    names=[x['destination'].casefold() for x in p['members']]
    assert len(names)==len(set(names))
    assert {'app/VERSION','app/scripts/tw_market_installation.py','app/frontend/unified-workbench/UnifiedMarketEvidenceWorkbench.html'} <= {x['destination'] for x in p['members']}
    for x in p['members']:assert (root/x['source']).is_file()
