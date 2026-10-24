import json,urllib.request,hashlib,concurrent.futures,zipfile,email,time
from pathlib import Path
from packaging.tags import cpython_tags,compatible_tags
from packaging.utils import parse_wheel_filename
from packaging.specifiers import SpecifierSet
ROOT=Path(r'C:\twmarket_temp\l7-a3\repo');O=ROOT.parent/'acquisition';O.mkdir(exist_ok=True); logs=[]
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((json.dumps(d,indent=2,sort_keys=True)+'\n').encode())
def get(url):
 for attempt in range(3):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'TW-Market-A3-freeze'}),timeout=50) as f:b=f.read()
   logs.append({'url':url,'phase':'setup','bytes':len(b),'attempt':attempt+1});return b
  except Exception as e:
   logs.append({'url':url,'phase':'setup','error':type(e).__name__,'attempt':attempt+1})
   if attempt==2:raise
rows=json.loads((ROOT/'packaging_native/wheelhouse-lock.json').read_bytes())['wheels']
versions={r['project']:r['version'] for r in rows};versions['playwright']='1.55.0'
def meta(item):
 n,v=item;p=O/'metadata'/(n+'.json');b=p.read_bytes() if p.exists() else get(f'https://pypi.org/pypi/{n}/{v}/json');p.parent.mkdir(exist_ok=True);p.write_bytes(b);return n,json.loads(b)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex: metadata=dict(ex.map(meta,versions.items()))
# Playwright's own upstream metadata fixes the two browser Python transitives.
from packaging.requirements import Requirement
for s in metadata['playwright']['info']['requires_dist']:
 r=Requirement(s)
 if r.marker is None or r.marker.evaluate({'python_version':'3.13','sys_platform':'linux','extra':''}):
  chosen={'pyee':'13.0.0','greenlet':'3.2.4'}[r.name];assert r.specifier.contains(chosen)
  n,d=meta((r.name,chosen));metadata[n]=d;versions[n]=d['info']['version']
print('metadata complete',len(metadata),flush=True)
def lock(py,platforms,consumer,browser=False):
 tags=list(cpython_tags(py,platforms=platforms))+list(compatible_tags(py,interpreter='cp'+''.join(map(str,py)),platforms=platforms));rank={t:i for i,t in reversed(list(enumerate(tags)))}; graph=[]
 names=list(versions if browser else {r['project']:r['version'] for r in rows})
 for n in sorted(names):
  if n=='pywin32' and platforms[0]!='win_amd64':continue
  d=metadata[n];assert SpecifierSet(d['info']['requires_python']).contains('.'.join(map(str,py))+'.9')
  matches=[]
  for f in d['urls']:
   if f['packagetype']!='bdist_wheel' or f['yanked']:continue
   wt=parse_wheel_filename(f['filename'])[3]; overlap=wt&rank.keys()
   if overlap:matches.append((min(rank[t] for t in overlap),f['filename'],f))
  assert matches,(n,py,platforms)
  f=sorted(matches,key=lambda x:x[:2])[0][2]
  graph.append(dict(name=n,version=d['info']['version'],wheel_filename=f['filename'],sha256=f['digests']['sha256'],url=f['url'],release_metadata_url=f'https://pypi.org/pypi/{n}/{d["info"]["version"]}/json',requires_python=d['info']['requires_python'],yanked=False))
 return dict(schema_version=1,consumer=consumer,python='.'.join(map(str,py)),platform=platforms[0],source='PyPI official release metadata',artifacts=graph,artifact_count=len(graph))
linux=[f'manylinux_2_{n}_x86_64' for n in range(39,16,-1)]+['manylinux2014_x86_64','manylinux2010_x86_64','manylinux1_x86_64','linux_x86_64']
locks=[lock((3,11),['win_amd64'],'developer-py311-windows'),lock((3,13),linux,'ci-py313-linux'),lock((3,13),linux,'browser-py313-linux',True)]
for l in locks:save(O/(l['consumer']+'.json'),l)
def artifact(item):
 directory,r=item;p=directory/r['wheel_filename'];p.parent.mkdir(parents=True,exist_ok=True)
 b=get(r['url']);assert hashlib.sha256(b).hexdigest()==r['sha256'];p.write_bytes(b)
for l in locks:
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as ex:list(ex.map(artifact,[(O/l['consumer'],r) for r in l['artifacts']]))
 print(l['consumer'],l['artifact_count'],'verified',flush=True)
save(O/'network.json',logs)
