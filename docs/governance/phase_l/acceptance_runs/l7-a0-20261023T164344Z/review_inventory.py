"""Offline review-only checks for this A0 ledger. Never changes product files."""
import collections
import hashlib
import json
from pathlib import Path
import subprocess

E = Path(__file__).resolve().parent
R = E.parents[4]
BASE = '125188604126bcdbfcfea0f6421eae6a160e9085'
FRONT = ['PROJECT.md', 'HANDOFF.md', 'ROADMAP.md', 'docs/governance/INDEX.md',
         'docs/governance/phase_l/PHASE_L_CURRENT_STATUS_AND_RECOVERY_INDEX_2026-10-14.md']
DOC = 'docs/governance/phase_l/PHASE_L_L7_A0_CI_RELEASE_CURRENT_STATE_INVENTORY_AND_GOVERNANCE_CONTRACT_2026-10-23.md'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def canonical(data):
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()

def load(name):
    return json.loads((E / (name + '.json')).read_text(encoding='utf-8'))

def git(*args):
    return subprocess.check_output(['git', *args], cwd=R, text=True).strip()

def verify_manifest(folder):
    m = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    expected = m.pop('self_digest')
    assert digest(canonical(m)) == expected, ('self_digest', str(folder))
    for item in m['members']:
        p = (folder / item['path']).resolve()
        assert p.is_relative_to(folder.resolve())
        b = p.read_bytes()
        assert len(b) == item['bytes'] and digest(b) == item['sha256'], item['path']
    return {'path':folder.relative_to(R).as_posix(), 'members':len(m['members']), 'self_digest':expected, 'status':'PASS'}

def review():
    changed = set(git('diff', '--name-only', BASE).splitlines())
    changed.update(git('ls-files', '--others', '--exclude-standard').splitlines())
    prefix = E.relative_to(R).as_posix() + '/'
    assert all(p in FRONT + [DOC] or p.startswith(prefix) for p in changed), sorted(changed)
    for p in changed:
        assert not p.lower().endswith(('.zip', '.whl', '.exe', '.dll', '.pyc', '.tar')), p
    failures = load('default_ci_failure_inventory')['nodes']
    classified = load('default_ci_failure_classification')
    assert len(failures) == len(classified['nodes']) == 45
    assert len({x['nodeid'] for x in failures}) == 45
    assert {x['nodeid'] for x in failures} == {x['nodeid'] for x in classified['nodes']}
    assert classified['aggregate_counts'] == dict(collections.Counter(x['classification'] for x in classified['nodes']))
    assert len(load('expanded_failure_classification')['nodes']) == 2
    assert len(load('candidate_l7_exit_criteria')['criteria']) == 29
    assert len(load('roadmap_l0_l7_obligation_matrix')['rows']) == 15
    profiles = json.loads((R / 'config/test_execution_profiles.json').read_text())['profiles']
    assert {x['name'] for x in load('test_profile_inventory')['profiles']} == set(profiles)
    assert {x['path'] for x in load('workflow_inventory')['workflows']} == {p.relative_to(R).as_posix() for p in (R / '.github/workflows').glob('*.yml')}
    gaps = load('gap_register')
    assert len(gaps['gaps']) == 22 and all(x['owner'] in ['A1','A2','A3','A4','A5','A6','A7','OUTSIDE_L7'] for x in gaps['gaps'])
    for item in load('source_inventory')['sources']:
        blob = subprocess.check_output(['git','cat-file','blob',BASE+':'+item['path']],cwd=R)
        assert digest(blob) == item['sha256'], item['path']
        assert git('rev-parse',BASE+':'+item['path']) == item['git_blob']
    for name in FRONT:
        text = (R/name).read_text(encoding='utf-8')
        assert 'L7-A0' in text[:4000] and 'OWNER ACCEPTANCE PENDING' in text[:4000], name
        assert 'L7-A1+' in text[:4000] and 'NOT AUTHORIZED' in text[:4000], name
    compile(Path(__file__).read_text(encoding='utf-8'), __file__, 'exec')
    return {'status':'PASS','changed_paths':sorted(changed),'allowed_front_doors':FRONT,'allowed_report':DOC,'allowed_evidence_prefix':prefix,'product_runtime_test_workflow_dependency_VERSION_changes':0,'review_harness_static':'PASS'}

if __name__ == '__main__':
    result = review()
    result['manifest'] = verify_manifest(E)
    print(json.dumps(result, ensure_ascii=False, indent=2))
