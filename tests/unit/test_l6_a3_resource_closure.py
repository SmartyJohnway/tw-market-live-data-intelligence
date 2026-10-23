"""Tests exercise the assembled allowlist, rather than the source checkout."""
import hashlib,io,json,os,shutil,subprocess,sys,zipfile
from pathlib import Path
import pytest
from scripts.build_native_distribution import inspect_wheels
ROOT=Path(__file__).parents[2]

def test_assembled_runtime_imports_and_version_without_git(tmp_path):
    policy=json.loads((ROOT/'packaging_native/resource-policy.json').read_text())
    app=tmp_path/'app'
    for e in policy['members']:
        if e['destination'].startswith('app/'):
            p=tmp_path/e['destination'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/e['source']).read_bytes())
    env=os.environ.copy();env.pop('PYTHONPATH',None);env.pop('PYTHONHOME',None);env['PYTHONDONTWRITEBYTECODE']='1';env['PATH']=str(Path(os.environ['SystemRoot'])/'System32')
    code="import sys,json,shutil,runpy;sys.path.insert(0,"+repr(str(app))+");import server.main;import scripts.m8r_05b_03.dispatch;from scripts.product_version import product_version;from scripts.m8r_03d_f1_security_master_snapshot_exporter import compute_skill_contract_hash;runpy.run_path("+repr(str(app/'scripts/m8r_06_01b_materialize_production_inputs.py'))+",run_name='_import_probe');print(json.dumps({'version':product_version(),'skill_hash':compute_skill_contract_hash(),'sys_path':sys.path,'git':shutil.which('git')}))"
    p=subprocess.run([sys.executable,'-I','-B','-c',code],env=env,cwd=tmp_path,capture_output=True,text=True,timeout=30)
    assert p.returncode==0,p.stderr
    result=json.loads(p.stdout)
    assert result['version']==(ROOT/'VERSION').read_text().strip()
    assert result['git'] is None
    assert not any(str(ROOT).lower() in x.lower() for x in result['sys_path'])
    from scripts.m8r_03d_f1_security_master_snapshot_exporter import compute_skill_contract_hash
    assert result['skill_hash']==compute_skill_contract_hash()

@pytest.mark.parametrize('tag',['cp312-cp312-win_amd64','cp313-cp313-win32','cp313-cp313-manylinux_2_17_x86_64'])
def test_incompatible_wheel_rejected(tmp_path,monkeypatch,tag):
    import scripts.build_native_distribution as mod
    monkeypatch.setattr(mod,'dependency_authority',lambda:{'example':'1.0'})
    with zipfile.ZipFile(tmp_path/f'example-1.0-{tag}.whl','w') as z:z.writestr('example-1.0.dist-info/METADATA','Name: example\nVersion: 1.0\n')
    monkeypatch.setattr(mod,'wheel_hash_authority',lambda:{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in tmp_path.iterdir()})
    with pytest.raises(ValueError):inspect_wheels(tmp_path)

def test_missing_dependency_rejected(tmp_path):
    with pytest.raises(ValueError,match='incomplete wheel'):inspect_wheels(tmp_path)


def test_runtime_agent_links_are_included():
    sources={x['source'] for x in json.loads((ROOT/'packaging_native/resource-policy.json').read_text())['members']}
    for name in ('references/capability_quick_guide.md','references/evidence_semantics.md',
                 'references/tool_selection_examples.md','references/current_limitations.md',
                 'assets/unified_capability_catalog_portable.json'):
        assert 'skills/tw-market-evidence-agent/'+name in sources


def test_same_name_version_wheel_substitution_is_rejected(tmp_path):
    with zipfile.ZipFile(tmp_path/'requests-2.34.2-py3-none-any.whl','w') as z:
        z.writestr('requests-2.34.2.dist-info/METADATA','Name: requests\nVersion: 2.34.2\n')
    with pytest.raises(ValueError,match='committed PyPI artifact authority'):
        inspect_wheels(tmp_path)
