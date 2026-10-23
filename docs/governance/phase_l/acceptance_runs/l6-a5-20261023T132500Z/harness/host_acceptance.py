"""Actual packaged P1/P4/P5 probes; host outputs stay in the A5 boundary."""
import argparse,asyncio,hashlib,json,os,pathlib,runpy,subprocess,sys,zipfile
ROOT=pathlib.Path(r'C:\twmarket_temp\l6-a5\final-run')
OUT=ROOT/'evidence-host-run4';OUT.mkdir(exist_ok=True)
def save(name,value):(OUT/(name+'.json')).write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stable_home(root):return {k:v for k,v in inventory(root).items() if not k.startswith('logs/')}
def inventory(root):return {p.relative_to(root).as_posix():sha(p) for p in sorted(root.rglob('*')) if p.is_file()} if root.exists() else {}
env=dict(os.environ)
for k in list(env):
    if k.startswith(('TW_MARKET_','UNIFIED_MARKET_','M8R_','PYTHONPATH','PYTHONHOME')):env.pop(k)
env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',TEMP=str(ROOT/'temp'),TMP=str(ROOT/'temp'))
os.environ.update(env)
runpy.run_path(str(ROOT/'host_guard.py'),run_name='_acceptance_guard')
commands=[]
def extract(archive,parent):
    assert not parent.exists()
    with zipfile.ZipFile(archive) as z:z.extractall(parent)
    return next(parent.iterdir())
def bootstrap(bundle):
    p=subprocess.run([sys.executable,'-B',str(bundle/'bootstrap/bootstrap.py'),'--bundle',str(bundle)],env=env,capture_output=True,text=True,encoding='utf-8',timeout=240)
    save('bootstrap-'+str(len(commands)),{'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr});commands.append('bootstrap')
    assert p.returncode==0,p.stderr
def command(bundle,name,home,*args):
    p=subprocess.run([str(bundle/'runtime/venv/Scripts/python.exe'),'-B',str(bundle/'bootstrap/launch.py'),'market',name,'--home',str(home),*args,'--json'],env=dict(env,A5_APP_ROOT=str(bundle/'app'),A5_READ_ONLY='1' if name in {'status','doctor'} else '0'),capture_output=True,text=True,encoding='utf-8',cwd=str(bundle),timeout=120)
    try:data=json.loads(p.stdout)
    except ValueError:data={'stdout':p.stdout}
    result={'command':name,'bundle':str(bundle),'home':str(home),'returncode':p.returncode,'result':data,'stderr':p.stderr}
    commands.append(result);save('command-'+str(len(commands)),result);return result
async def mcp(bundle,home,port):
    sys.path.insert(0,str(ROOT/'sandbox/input'))
    from raw_stdio import probe
    return probe(bundle/'runtime/venv/Scripts/python.exe',['-B',bundle/'bootstrap/launch.py','mcp','--home',home,'--service-url',f'http://127.0.0.1:{port}'],dict(env,TW_MARKET_HOME=str(home),A5_APP_ROOT=str(bundle/'app')),bundle)
def lifecycle(bundle,home,port):
    assert command(bundle,'start',home,'--port',str(port))['returncode']==0
    try:
        status=command(bundle,'status',home,'--port',str(port));assert status['returncode']==0;before=stable_home(home)
        doctor=command(bundle,'doctor',home,'--port',str(port));assert doctor['returncode']==0;assert stable_home(home)==before
        tools=asyncio.run(mcp(bundle,home,port))
        return {'status':status,'doctor':doctor,'mcp':tools,'doctor_read_only':True}
    finally:command(bundle,'stop',home,'--port',str(port))
def main():
    archive=ROOT/'build/native-source-final/TW-Market-1.0.0-windows-x64.zip'
    a=extract(archive,ROOT/'native-run4/App A');bootstrap(a)
    home=ROOT/'installations/p1-home-run4';state=ROOT/'installations/p1-state-run4'
    command(a,'status',home);command(a,'doctor',home);assert not home.exists()
    assert command(a,'init',home,'--state-root',str(state))['returncode']==0
    meta=(home/'meta/installation.json').read_bytes();settings=sha(home/'config/settings.json')
    (state/'governed/relocation-canary.json').write_text('{"acceptance_only":true}\n')
    state_before=inventory(state);app_a=inventory(a/'app')
    first=lifecycle(a,home,18451);assert inventory(a/'app')==app_a
    moved=ROOT/'native-run4/retired App A'
    os.rename(a.parent,moved)
    env['A5_FORBIDDEN_READ_PREFIX']=str(a)
    b=extract(archive,ROOT/'native-run4/深層 路徑/application B/deeper');bootstrap(b)
    app_b=inventory(b/'app');second=lifecycle(b,home,18451)
    assert inventory(b/'app')==app_b and (home/'meta/installation.json').read_bytes()==meta
    assert sha(home/'config/settings.json')==settings and inventory(state)==state_before
    save('p1_relocation',{'status':'PASS','app_a':str(a),'app_b':str(b),'old_root_unavailable':not a.exists(),'home':str(home),'state':str(state),'metadata_sha256':hashlib.sha256(meta).hexdigest(),'settings_sha256':settings,'state_hashes':state_before,'first':first,'second':second,'app_root_unchanged':True})
    save('packaged-runtime-paths',{'bundle':str(b),'python':str(b/'runtime/venv/Scripts/python.exe'),'home':str(home)})
if __name__=='__main__':
    try:main()
    except Exception as exc:
        save('host-acceptance-failed',{'type':type(exc).__name__,'error':str(exc)});raise
