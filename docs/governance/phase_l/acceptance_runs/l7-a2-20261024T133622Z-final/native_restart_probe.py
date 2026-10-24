import os,sys,json,subprocess,socket,hashlib
from pathlib import Path
BASE=Path(r'C:\twmarket_temp\l7-a2\continuation')
RUN=BASE/'final-source/native-quiet'
BUNDLE=RUN/'Location-B/TW-Market-1.0.0-windows-x64'
OUT=BASE/'native-restart';OUT.mkdir();(OUT/'outside cwd').mkdir()
installation=json.loads((RUN/'initialized_package_acceptance.json').read_text(encoding='utf-8'))['installation']
env={k:v for k,v in os.environ.items() if not k.startswith(('TW_MARKET_','UNIFIED_MARKET_','M8R_','PYTHON'))}
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
env.update(TEMP=str(RUN/'tmp'),TMP=str(RUN/'tmp'),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PATH=r'C:\Windows\System32;C:\Windows',TW_MARKET_HOME=installation['home'],TW_MARKET_STATE_ROOT=installation['state_root'],LOCALAPPDATA=str(RUN/'isolated-localappdata'),TW_MARKET_HOST='127.0.0.1',TW_MARKET_PORT=str(port),UNIFIED_MARKET_EVIDENCE_SERVICE_URL='http://127.0.0.1:'+str(port),TW_MARKET_ACCEPTANCE_GUARD='1',TW_MARKET_ACCEPTANCE_GUARD_BASE=r'C:\twmarket_temp\l7-a2',TW_MARKET_GUARD_LOG=str(OUT/'guard.jsonl'))
os.environ.update(env)
guard=RUN/'acceptance_guard.py';exec(compile(guard.read_bytes(),str(guard),'exec'),{'__file__':str(guard)})
def fingerprint(root,exclude_logs=False):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file() and not (exclude_logs and p.relative_to(root).parts[0]=='logs')}
def business():return {'HOME':fingerprint(Path(installation['home']),True),'STATE':fingerprint(Path(installation['state_root']))}
before=business();app_before=fingerprint(BUNDLE/'app');records=[]
def cli(command):
    line='"C:\\Windows\\System32\\cmd.exe" /d /s /c ""'+str(BUNDLE/'tw-market.cmd')+'" '+command+' --json"'
    p=subprocess.run(line,cwd=OUT/'outside cwd',env=env,capture_output=True,text=True,encoding='utf-8',timeout=150)
    row={'command':command,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr};records.append(row)
    (OUT/'commands.json').write_bytes((json.dumps(records,indent=2)+'\n').encode())
    assert p.returncode==0,row
    return json.loads(p.stdout)
try:
    first=cli('start');assert first['status']=='STARTED'
    first_status=cli('status');assert first_status['service']['alive'] and first_status['service']['process']=='RUNNING'
    assert cli('stop')['status']=='STOPPED'
    second=cli('start');assert second['status']=='STARTED' and second['pid']!=first['pid']
    second_status=cli('status');assert second_status['service']['alive'] and second_status['service']['process']=='RUNNING'
    readonly=business();doctor=cli('doctor');assert business()==readonly
    assert second_status['installation']['installation_id']==installation['installation_id']
    assert cli('stop')['status']=='STOPPED'
    assert business()==before and fingerprint(BUNDLE/'app')==app_before
    assert not (OUT/'guard.jsonl').exists()
    result={'status':'PASS','source_commit':'510625c8e81e629e2c902b17949aa155abfe78b6','contract':'restart via existing stop/start commands; no new public restart entry point','first_pid':first['pid'],'replacement_pid':second['pid'],'installation_id':installation['installation_id'],'business_state_unchanged':True,'doctor_read_only':True,'app_immutable':True,'guard_denials':0,'records':records}
    (OUT/'result.json').write_bytes((json.dumps(result,indent=2)+'\n').encode())
finally:
    try:cli('stop')
    except Exception:pass
