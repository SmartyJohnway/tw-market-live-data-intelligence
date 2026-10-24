"""Expected denial controls, separate from the product test execution window."""
import json
import os
from pathlib import Path
import subprocess
import sys

B=Path(__file__).parent;R=B/'repo';O=B/'negative-controls-final';O.mkdir(exist_ok=True)
guard=R/'scripts/deterministic_ci_guard.py'
probes={
 'dns':"import socket;socket.getaddrinfo('example.invalid',443)",
 'socket_connect_ex':"import socket;socket.socket().connect_ex(('192.0.2.1',443))",
 'urllib':"import urllib.request;urllib.request.urlopen('https://example.invalid')",
 'requests':"import requests;requests.get('https://example.invalid')",
 'httpx':"import httpx;httpx.get('https://example.invalid')",
 'isolated_python_child':"import subprocess,sys;sys.exit(subprocess.run([sys.executable,'-I','-S','-c',\"import socket;socket.socket().connect(('192.0.2.1',443))\"]).returncode)",
 'native_child':"import subprocess;subprocess.run(['curl','https://example.invalid'])",
 'node_https':"import subprocess;subprocess.run([r'C:\\Program Files\\nodejs\\node.exe','-e',\"require('node:https').get('https://example.invalid')\",'workbench-state.js'],check=True)",
 'node_worker':"import subprocess;subprocess.run([r'C:\\Program Files\\nodejs\\node.exe','-e',\"new (require('node:worker_threads').Worker)('process.exit(0)',{eval:true})\",'workbench-state.js'],check=True)",
}
rows=[]
for name,code in probes.items():
 log=O/(name+'.jsonl');assert not log.exists()
 env=os.environ.copy();env.update(TW_MARKET_CI_GUARD_LOG=str(log),TW_MARKET_CI_BOUND=str(B),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
 for k in list(env):
  if k.lower() in {'http_proxy','https_proxy','all_proxy'}:env.pop(k)
 pre='import runpy;runpy.run_path('+repr(str(guard))+',run_name="_deterministic_ci_guard");'
 p=subprocess.run([sys.executable,'-c',pre+code],cwd=R,env=env,text=True,capture_output=True,timeout=30)
 events=[json.loads(x) for x in log.read_text(encoding='utf-8').splitlines()]
 denied=[x for x in events if x['event']=='denied']
 rows.append({'probe':name,'returncode':p.returncode,'expected_denials':denied,'guarded_processes':[x for x in events if x['event'].startswith('guard_loaded')],'status':'PASS' if p.returncode!=0 and len(denied)==1 else 'FAIL'})
 (O/(name+'.stderr.txt')).write_text(p.stderr,encoding='utf-8',newline='\n')
print(json.dumps(rows,indent=2))
(O/'result.json').write_text(json.dumps({'window':'intentional guard negative controls; not product execution','probes':rows,'real_external_dispatches':0},indent=2)+'\n',encoding='utf-8',newline='\n')
assert all(x['status']=='PASS' for x in rows)
