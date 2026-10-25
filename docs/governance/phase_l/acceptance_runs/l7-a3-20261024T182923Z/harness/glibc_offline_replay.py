from pathlib import Path
import sys,json,subprocess
sys.path.insert(0,str(Path.cwd()))
from scripts.dependency_authority import load_consumer,requirements,verify_artifacts
r=Path.cwd().parent;out=r/'glibc-replay';out.mkdir();c,rows=load_consumer('browser-linux');verify_artifacts(rows,r/'acquisition/browser-py313-linux');(out/'requirements.txt').write_bytes(requirements(rows).encode())
docker=r'C:\Users\weitang\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe';name='tw-market-l7-a3-glibc-replay';base='python@sha256:e32be0e55814a08977501ca863271d9bd02443710db8f2afaf8372e2c4508530'
results=[]
def run(*args):
 p=subprocess.run([docker,*args],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=240);results.append(dict(args=args,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));(out/'commands.json').write_bytes((json.dumps(results,indent=2)+'\n').encode());assert p.returncode==0,args;return p
code="import subprocess,sys,json;subprocess.run([sys.executable,'-m','venv','/a3-venv'],check=True);p='/a3-venv/bin/python';subprocess.run([p,'-m','pip','install','--disable-pip-version-check','--no-index','--no-deps','--no-cache-dir','--no-compile','--only-binary=:all:','--require-hashes','--find-links','/a3-wheels','-r','/a3-requirements.txt'],check=True);subprocess.run([p,'-m','pip','check'],check=True);subprocess.run([p,'-c','import fastapi,pandas,numpy,mcp,playwright;print(\"A3_GLIBC_IMPORTS_PASS\")'],check=True)"
run('create','--name',name,'--network','none','--entrypoint','python',base,'-c',code)
try:
 run('cp',str(r/'acquisition/browser-py313-linux'),name+':/a3-wheels');run('cp',str(out/'requirements.txt'),name+':/a3-requirements.txt');run('start','-a',name);run('inspect',name)
finally:run('rm',name)
print('glibc browser graph offline replay and imports PASS')
