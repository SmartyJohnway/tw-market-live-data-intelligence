from pathlib import Path
import json,hashlib,subprocess,sys,os,base64,platform,zlib,xml.etree.ElementTree as ET
r=Path(r'C:\twmarket_temp\l7-a3\repo');p=r.parent;sys.path.insert(0,str(r))
from scripts.dependency_authority import load_consumer,verify_artifacts,canonical,sbom
from scripts.validate_dependency_authority import validate
assert validate()['status']=='PASS'
def j(f):return json.loads(Path(f).read_text(encoding='utf-8-sig'))
def sh(b):return hashlib.sha256(b).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=r)
assert git('rev-parse','HEAD').decode().strip()=='ab2b2dc941aea68187145166a519757622d092e8'
assert not git('status','--porcelain')
base='5c62d6d8cc6c49b2803126aa2190a1778fa1d4ac';source='ab2b2dc941aea68187145166a519757622d092e8';tree='1ccdb3e77ca99972d965a3f7eb771d2807fd7e73'
old=r/'docs/governance/phase_l/acceptance_runs/l7-a2-20261024T133622Z-final'
gate=p/'gate313-final/release-blocking-ci';assert j(gate/'result.json')['status']=='PASS';assert j(gate/'members.json')==j(old/'release_blocking_ci_members.json')
assert not j(gate/'result.json')['guard_denials']
host=p/'native acceptance 最終';assert j(host/'final_result.json')['status']=='PASS' and not j(host/'final_result.json')['guard_events']
guest=p/'sandbox/output';assert j(guest/'result.json')['status']=='PASS' and j(guest/'result.json')['acceptance_exit']==0
assert j(guest/'result.json')['source_commit']==source and not j(guest/'acceptance/final_result.json')['guard_events']
docker=p/'docker-acceptance-final';assert j(docker/'result.json')['status']=='PASS'
assert j(docker/'result.json')['before']==j(docker/'result.json')['after']
assert j(p/'runtime311-native-guard-v2/result.json')['status']=='PASS' and not j(p/'runtime311-native-guard-v2/result.json')['guard_denials']
assert j(p/'compatibility311-probe/result.json')['exit_code']==0 and not j(p/'compatibility311-probe/result.json')['guard_denials']
assert j(p/'final-validators/result.json')['status']=='PASS'
# Every release/compatibility wheel must independently match current official metadata.
metadata={}
for f in (p/'acquisition/metadata').glob('*.json'):
 d=j(f);metadata[d['info']['name'].lower().replace('_','-')]=(d,f)
checks=[]
for consumer in j(r/'config/dependency_authority.json')['consumers']:
 c,rows=load_consumer(consumer)
 cache={'native-windows':'artifacts/windows','release-ci-windows':'artifacts/windows','docker-linux':'artifacts/linux','ci-linux':'acquisition/ci-py313-linux','browser-linux':'acquisition/browser-py313-linux','developer-py311-windows':'acquisition/developer-py311-windows'}[consumer]
 verify_artifacts(rows,p/cache)
 for row in rows:
  name=row.get('name',row.get('project')).lower().replace('_','-');d,f=metadata[name]
  matches=[x for x in d['urls'] if x['filename']==row['wheel_filename'] and x['digests']['sha256']==row['sha256']]
  assert len(matches)==1 and not matches[0]['yanked'] and matches[0]['packagetype']=='bdist_wheel'
  checks.append(dict(consumer=consumer,artifact=row['wheel_filename'],sha256=row['sha256'],official_metadata_sha256=sh(f.read_bytes()),source=row['release_metadata_url'],yanked=False,binary_wheel=True))
(p/'artifact-authority-verification.json').write_bytes((json.dumps(checks,indent=2)+'\n').encode())
# Verify installed canonical/compatibility closure; bundled pip/setuptools are prerequisite tooling.
environments=[]
for name in ['venv311','venv313']:
 exe=str(p/name/'Scripts/python.exe');code="import sys,importlib.metadata as m,json;print(json.dumps(dict(python=sys.version,packages={d.metadata['Name'].lower().replace('_','-'):d.version for d in m.distributions()})))"
 d=json.loads(subprocess.check_output([exe,'-B','-c',code],text=True,encoding='utf-8'))
 consumer='developer-py311-windows' if name=='venv311' else 'release-ci-windows';_,rows=load_consumer(consumer)
 expected={x.get('name',x.get('project')).lower().replace('_','-'):x['version'] for x in rows}
 assert all(d['packages'].get(k)==v for k,v in expected.items());extra=set(d['packages'])-set(expected);assert extra<={'pip','setuptools'}
 d.update(consumer=consumer,application_graph_equal=True,prerequisite_tooling={k:d['packages'][k] for k in extra});environments.append(d)
(p/'installed-graph-verification.json').write_bytes((json.dumps(environments,indent=2)+'\n').encode())
# Validate Debian replay actual container exit and import witness, not only Docker CLI success.
commands=j(p/'glibc-replay/commands.json');inspect=next(x for x in commands if x['args'][0]=='inspect');container=json.loads(inspect['stdout'])[0];assert container['State']['ExitCode']==0
start=next(x for x in commands if x['args'][0]=='start');assert 'A3_GLIBC_IMPORTS_PASS' in start['stdout']
assert j(p/'docker-reproducibility-clean/comparison.json')['status']=='PASS'
assert j(p/'native-final-a.json')['sha256']==j(p/'native-final-b.json')['sha256']
print('Final facts validated: all core acceptance PASS, six consumer artifact authorities verified, installed graphs exact, A1 membership unchanged')
