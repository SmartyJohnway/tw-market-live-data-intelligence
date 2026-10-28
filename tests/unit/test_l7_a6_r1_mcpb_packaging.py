"""Bounded offline MCPB authority regressions, outside frozen A1 membership."""
import copy
import json
from pathlib import Path
import zipfile

import pytest
from scripts import build_mcpb_distribution as b
from packaging_mcpb.record import canonical_record


@pytest.mark.parametrize('field,expected',[
    ('manifest_version','0.3'),('version','1.5.0'),('name','tw-market-unified-mcp')])
def test_manifest_identity(field,expected):
    assert b.manifest('1.5.0')[field]==expected


def test_windows_python_stdio_and_exact_six():
    m=b.manifest('1.5.0')
    assert m['compatibility']=={'platforms':['win32'],'runtimes':{'python':'>=3.13,<3.14'}}
    assert m['server']['type']=='python'
    assert m['server']['mcp_config']['command']=='python'
    assert {t['name'] for t in m['tools']}==b.canonical_tools()==b.TOOLS
    assert m['server']['entry_point']=='app/scripts/run_unified_market_evidence_mcp.py'


@pytest.mark.parametrize('kind',['extra','stale','duplicate','version','platform'])
def test_manifest_rejects_disagreement(kind):
    m=copy.deepcopy(b.manifest('1.5.0'))
    if kind=='extra': m['tools'].append({'name':'seventh'})
    if kind=='stale': m['tools'][0]['name']='historical'
    if kind=='duplicate': m['tools'].append(m['tools'][0])
    if kind=='version': m['version']='1.0.0'
    if kind=='platform': m['compatibility']['platforms']=['linux']
    with pytest.raises(ValueError): b.validate_manifest(m)


def test_archive_and_sidecar_reproducibility(tmp_path):
    payload={'z.txt':b'z','manifest.json':b.canonical(b.manifest('1.5.0')),'app/x.py':b'x'}
    a,bp=tmp_path/'a.mcpb',tmp_path/'b.mcpb'
    b.write_archive(a,payload); b.write_archive(bp,dict(reversed(list(payload.items()))))
    assert a.read_bytes()==bp.read_bytes()
    assert (b.digest(a.read_bytes())+'  '+b.FILENAME+'\n').encode()==(b.digest(bp.read_bytes())+'  '+b.FILENAME+'\n').encode()
    with zipfile.ZipFile(a) as z:
        assert z.namelist()==sorted(payload)
        assert all(i.date_time==(1980,1,1,0,0,0) for i in z.infolist())
        assert all(i.external_attr==0o100644<<16 for i in z.infolist())


@pytest.mark.parametrize('name',['../escape','C:/private','/absolute','a\\b'])
def test_unsafe_members_rejected(tmp_path,name):
    with pytest.raises(ValueError): b.write_archive(tmp_path/'bad.zip',{name:b'x'})


@pytest.mark.parametrize('data',[b'C:\\twmarket_temp\\private',b'D:\\private',b'-----BEGIN PRIVATE KEY-----',b'github_pat_'+b'a'*40])
def test_first_party_hygiene(data):
    with pytest.raises(ValueError) as exc: b.check_member('app/x.txt',data)
    assert data.decode() not in str(exc.value)


def test_missing_wheel_fails_closed(tmp_path,monkeypatch):
    monkeypatch.setattr(b,'git',lambda *args: b'' if args[0]=='diff' else b'1.5.0\n')
    with pytest.raises(ValueError,match='MCPB_WHEELHOUSE_INCOMPLETE'):
        b.build(tmp_path/'external',tmp_path/'missing')


def test_current_registry_metadata_stays_published_v1():
    v=json.loads((b.ROOT/'server.json').read_bytes())
    assert v['version']=='1.0.0'
    assert 'v1.0.0/' in v['packages'][0]['identifier']


def test_packaging_is_test_authority_until_r2():
    p=json.loads((b.ROOT/'packaging_mcpb/resource-policy.json').read_bytes())
    assert p['artifact_purpose']=='TEST_ONLY_UNTIL_R2_EXACT_SOURCE_RECERTIFICATION'
    assert p['dependency_authority']=='packaging_native/wheelhouse-lock.json'
    assert p['dependency_root']=='server/lib'


def test_record_recomputes_final_bytes_and_is_idempotent():
    own='demo.dist-info/RECORD'; payload={'demo.py':b'final',own:b''}
    before=dict(payload)
    data,omitted=canonical_record(b'demo.py,,1\r\ndemo.dist-info/RECORD,,\r\n',own,payload)
    assert b'sha256=' in data and b',5\n' in data
    assert b'demo.dist-info/RECORD,,\n' in data and b'\r' not in data
    assert canonical_record(data,own,payload)[0]==data
    assert payload==before and not omitted


def test_record_root_order_and_separator_independent():
    own='demo.dist-info/RECORD'; p={'demo/x.py':b'x',own:b''}
    a=b'demo\\x.py,,\r\ndemo.dist-info/RECORD,,\r\n'
    c=b'demo.dist-info/RECORD,,\ndemo/x.py,,\n'
    assert canonical_record(a,own,p)[0]==canonical_record(c,own,p)[0]


@pytest.mark.parametrize('bad',[
    b'x.py,,\nx.py,,\ndemo.dist-info/RECORD,,\n',
    b'demo\\x.py,,\ndemo/x.py,,\ndemo.dist-info/RECORD,,\n',
    b'../escape,,\ndemo.dist-info/RECORD,,\n',
    b'missing.py,,\ndemo.dist-info/RECORD,,\n',
    b'x.py,md5=abc,1\ndemo.dist-info/RECORD,,\n',
    b'x.py,broken,extra,column\n',
    b'C:/absolute,,\ndemo.dist-info/RECORD,,\n'])
def test_record_fail_closed(bad):
    with pytest.raises(ValueError,match='MCPB_RECORD_CANONICALIZATION_INVALID'):
        canonical_record(bad,'demo.dist-info/RECORD',{'x.py':b'x','demo/x.py':b'x','demo.dist-info/RECORD':b''})


def test_only_declared_non_distributed_launchers_may_be_omitted():
    own='demo.dist-info/RECORD'; p={own:b''}
    data=b'../../bin/demo.exe,,\ndemo.dist-info/RECORD,,\n'
    result,observations=canonical_record(data,own,p,{'../../bin/demo.exe'})
    assert result==b'demo.dist-info/RECORD,,\n'
    assert observations==[{'path':'../../bin/demo.exe','classification':'DECLARED_NON_DISTRIBUTED_PIP_LAUNCHER'}]
    with pytest.raises(ValueError): canonical_record(data,own,p)


def test_proven_binary_path_is_nonblocking_but_unproven_is_blocking():
    from packaging_mcpb.hygiene import scan
    data=b'MZ\0D:\\upstream-builder\\project\\module.pdb\0'
    provenance={'wheel':'accepted.whl','wheel_sha256':'a'*64,'member_sha256':b.digest(data)}
    rows=scan('server/lib/module.pyd',data,provenance)
    assert rows and all(not r['blocking'] for r in rows)
    assert all(r['classification']=='NONBLOCKING_UPSTREAM_BUILD_PROVENANCE' for r in rows)
    assert all(r['blocking'] for r in scan('server/lib/module.pyd',data))
    assert 'upstream-builder' not in json.dumps(rows)


def test_binary_provenance_does_not_excuse_secret_or_current_worktree():
    from packaging_mcpb.hygiene import scan
    for data in (b'MZ\0github_pat_'+b'a'*40,b'MZ\0C:\\twmarket_temp\\private\\x.pdb\0'):
        provenance={'wheel':'accepted.whl','wheel_sha256':'a'*64,'member_sha256':b.digest(data)}
        assert any(r['blocking'] for r in scan('server/lib/module.pyd',data,provenance))


def test_nonrecord_members_unchanged_in_real_normalization(tmp_path):
    from packaging_mcpb.record import normalize_installed
    lib=tmp_path/'lib'; lib.mkdir()
    (lib/'demo.py').write_bytes(b'unchanged source')
    meta=lib/'demo-1.dist-info'; meta.mkdir()
    (meta/'RECORD').write_bytes(b'demo.py,,\ndemo-1.dist-info/RECORD,,\n')
    wheel=tmp_path/'demo.whl'
    with zipfile.ZipFile(wheel,'w') as z:
        z.writestr('demo-1.dist-info/RECORD','')
    dependencies=[{'wheel_filename':wheel.name}]
    before=(lib/'demo.py').read_bytes()
    normalize_installed(lib,tmp_path,dependencies)
    first=(meta/'RECORD').read_bytes()
    normalize_installed(lib,tmp_path,dependencies)
    assert (meta/'RECORD').read_bytes()==first
    assert (lib/'demo.py').read_bytes()==before


@pytest.mark.parametrize('value',[
    r'C:\Users\weitang\private\key.txt',r'C:\twmarket_temp\work\private.txt',
    r'D:\Codex-Workspace\secret.txt',r'%LOCALAPPDATA%\TW-Market\state.json',
    'file:///C:/Users/weitang/private.txt','file:///C:/twmarket_temp/private.txt'])
@pytest.mark.parametrize('name',['app/example.py','server/lib/numpy/__config__.py'])
def test_semantic_current_host_remains_blocking(monkeypatch,name,value):
    from packaging_mcpb.hygiene import scan
    monkeypatch.setenv('USERNAME','weitang')
    data=value.encode()
    prov={'wheel':'accepted.whl','wheel_sha256':'a'*64,'member_sha256':b.digest(data),'origin_wheel_member':name}
    assert any(r['blocking'] for r in scan(name,data,prov))


@pytest.mark.parametrize('value',[r'%d:\n',r'\d\d:\d\d'])
def test_semantic_regex_and_printf_are_not_paths(value):
    from packaging_mcpb.hygiene import scan
    assert scan('server/lib/pygments/lexers/configs.py',value.encode())==[]


@pytest.mark.parametrize('value',[r'C:\foo\bar.txt','file:///',r'C:\Windows\System32','C:\\Users\\','D:\\'])
def test_semantic_generic_example_is_not_host_leakage(value):
    from packaging_mcpb.hygiene import scan
    data=value.encode()
    prov={'wheel':'accepted.whl','wheel_sha256':'a'*64,'member_sha256':b.digest(data),'origin_wheel_member':'requests/utils.py'}
    rows=scan('server/lib/requests/utils.py',data,prov)
    assert rows and all(not r['blocking'] for r in rows)
    assert all(r['classification']=='GENERIC_PATH_OR_URI_EXAMPLE' for r in rows)


def test_generated_source_and_authoring_metadata_require_exact_provenance():
    from packaging_mcpb.hygiene import scan
    cases=[('server/lib/win32/lib/win32con.py',b'# Generated by h2py from d:\\mssdk\\include\\win32.h',
            'NONBLOCKING_UPSTREAM_GENERATED_SOURCE_PROVENANCE'),
           ('server/lib/win32com/HTML/PythonCOM.html',b'<META NAME="Template" CONTENT="D:\\Program Files\\Microsoft Office\\Office\\html.dot">',
            'NONBLOCKING_UPSTREAM_DOCUMENT_AUTHORING_PROVENANCE')]
    for name,data,expected in cases:
        prov={'wheel':'accepted.whl','wheel_sha256':'a'*64,'member_sha256':b.digest(data),'origin_wheel_member':name}
        rows=scan(name,data,prov)
        assert rows and all(not r['blocking'] and r['classification']==expected for r in rows)
        assert any(r['blocking'] for r in scan(name,data))
        injected=data+b'\nC:\\twmarket_temp\\private.txt'
        prov['member_sha256']=b.digest(injected)
        assert any(r['blocking'] for r in scan(name,injected,prov))


def test_new_upstream_text_not_in_authorized_semantics_stays_blocking():
    from packaging_mcpb.hygiene import scan
    data=b'D:\\old-developer\\private.txt'
    prov={'wheel':'accepted.whl','wheel_sha256':'a'*64,'member_sha256':b.digest(data),'origin_wheel_member':'other.py'}
    assert any(r['blocking'] for r in scan('server/lib/other.py',data,prov))


def test_semantic_class_never_downgrades_secret():
    from packaging_mcpb.hygiene import scan
    data=b'file:/// github_pat_'+b'a'*40
    prov={'wheel':'accepted.whl','wheel_sha256':'a'*64,'member_sha256':b.digest(data),'origin_wheel_member':'requests/utils.py'}
    rows=scan('server/lib/requests/utils.py',data,prov)
    assert any(r['blocking'] and r['classification']=='SECRET_MATERIAL' for r in rows)
