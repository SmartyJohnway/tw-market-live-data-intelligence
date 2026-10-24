"""Fail-closed static dependency, SBOM and action identity contract checks."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.dependency_authority import load_consumer, canonical, sbom


def validate(root=ROOT):
    policy=json.loads((root/'config/dependency_authority.json').read_bytes())
    assert policy['python_policy']['canonical']=='CPython 3.13'
    assert policy['python_policy']['unsupported']==['3.12']
    assert '3.11' in policy['python_policy']['compatibility']
    assert policy['python_policy']['native_tier1']=='Windows 11 x64'
    assert not policy['replay']['index'] and not policy['replay']['transitive_resolution']
    expected={'developer-py311-windows','release-ci-windows','native-windows','ci-linux','docker-linux','browser-linux'}
    assert set(policy['consumers'])==expected
    graphs={}
    for name in sorted(expected):
        consumer, rows=load_consumer(name,root)
        graphs[name]={r.get('name',r.get('project')).lower().replace('_','-'):r['version'] for r in rows}
        assert consumer['python']==('3.11' if name=='developer-py311-windows' else '3.13')
        assert all(not r.get('url') or r['url'].startswith('https://files.pythonhosted.org/') for r in rows)
    baseline=graphs['native-windows']
    assert graphs['release-ci-windows']==baseline
    assert graphs['developer-py311-windows']==baseline
    for name in ('docker-linux','ci-linux'):
        assert graphs[name]=={n:v for n,v in baseline.items() if n!='pywin32'}
    assert {n:v for n,v in graphs['browser-linux'].items() if n not in {'playwright','pyee','greenlet'}}==graphs['ci-linux']
    assert graphs['browser-linux']['playwright']=='1.55.0'
    projection={}
    for line in (root/'requirements-lock.txt').read_text().splitlines():
        if not line or line.startswith('#'):continue
        name,version=line.split(';')[0].strip().split('==')
        projection[name.lower().replace('_','-')]=version
    assert projection==baseline
    sha=hashlib.sha256((root/'requirements-lock.txt').read_bytes()).hexdigest()
    assert json.loads((root/'packaging_native/wheelhouse-lock.json').read_bytes())['requirements_lock_sha256']==sha
    assert json.loads((root/'packaging_docker/dependency-lock-linux-amd64-cp313.json').read_bytes())['source_requirements_sha256']==sha
    actions=json.loads((root/'config/github_actions_artifact_authority.json').read_bytes())
    approved={n+'@'+v['sha'] for n,v in actions['actions'].items()}
    for row in actions['actions'].values():
        assert re.fullmatch('[0-9a-f]{40}',row['sha'])
        assert row['ref_url'].startswith('https://api.github.com/repos/actions/')
        assert row['commit_url'].endswith(row['sha'])
    for path in (root/'.github/workflows').glob('*.yml'):
        text=path.read_text()
        uses=re.findall(r'^\s*-?\s*uses:\s*(\S+)',text,re.M)
        assert uses and set(uses)<=approved,'unverified or mutable action'
        assert '3.11' not in text, 'canonical hosted runtime drift'
        for token in ('ImageOS','ImageVersion','RUNNER_OS','RUNNER_ARCH'):
            assert token in text,'runner provenance missing'
        assert 'pip install -r requirements.txt' not in text
        assert 'pip install --upgrade pip' not in text
    assert canonical(sbom(root))==(root/'config/first_party_dependency_sbom.json').read_bytes()
    browser=json.loads((root/'config/browser_artifact_authority.json').read_bytes())
    assert browser['playwright_version']==graphs['browser-linux']['playwright']
    assert {r['name'] for r in browser['artifacts']}=={'chromium','chromium-headless-shell','ffmpeg'}
    for row in browser['artifacts']:
        assert re.fullmatch('[0-9a-f]{64}',row['sha256']) and row['bytes']>0
        assert row['url'].startswith('https://cdn.playwright.dev/')
        assert '/'+row['revision']+'/' in row['url']
    return {'status':'PASS','consumers':len(expected),'core_package_version_changes':0,
            'sbom_sha256':hashlib.sha256(canonical(sbom(root))).hexdigest()}


if __name__=='__main__':
    print(json.dumps(validate(),indent=2))
