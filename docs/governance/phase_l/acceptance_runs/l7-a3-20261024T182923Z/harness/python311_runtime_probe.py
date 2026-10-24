import os,sys,json,subprocess,socket,queue,threading,hashlib
from pathlib import Path
root=Path(r'C:\twmarket_temp\l7-a3\repo');out=root.parent/'runtime311-native-guard-v2';out.mkdir();os.chdir(root);sys.path.insert(0,str(root))
for n in ['home','state','temp','local']:(out/n).mkdir()
os.environ.update(TW_MARKET_CI_NODE=r'C:\Program Files\nodejs\node.exe',TW_MARKET_CI_BOUND=str(root.parent),TW_MARKET_CI_GUARD_LOG=str(out/'guard.jsonl'),TW_MARKET_HOME=str(out/'home'),TW_MARKET_STATE_ROOT=str(out/'state'),LOCALAPPDATA=str(out/'local'),TEMP=str(out/'temp'),TMP=str(out/'temp'),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
os.environ.update(COMSPEC=r'C:\Windows\System32\cmd.exe',TW_MARKET_ACCEPTANCE_GUARD='1',TW_MARKET_ACCEPTANCE_GUARD_BASE=str(root.parent),TW_MARKET_GUARD_LOG=str(out/'guard.jsonl'),A3_NATIVE_IDENTITY_LOG=str(out/'native-identity.jsonl'))
g=Path(r'C:\twmarket_temp\l7-a3\compatibility311-native-guard-v2.py');exec(compile(g.read_text(),str(g),'exec'),{'__file__':str(g)})
with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
os.environ['TW_MARKET_PORT']=str(port);os.environ['UNIFIED_MARKET_EVIDENCE_SERVICE_URL']=f'http://127.0.0.1:{port}'
sequence=[]
def save(n,x):(out/(n+'.json')).write_bytes((json.dumps(x,indent=2,ensure_ascii=False)+'\n').encode())
def cli(label,*args):
 p=subprocess.run([sys.executable,'-B','scripts/tw_market_lifecycle.py',*args,'--home',str(out/'home'),'--state-root',str(out/'state'),'--port',str(port),'--json'],capture_output=True,text=True,encoding='utf-8',timeout=120)
 save(label,dict(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));sequence.append(dict(label=label,exit_code=p.returncode));return json.loads(p.stdout)
result={'status':'FAIL'}
try:
 pre=cli('preinit','status');assert pre['status']=='INSTALLATION_NOT_INITIALIZED';assert not (out/'home/installation.json').exists()
 one=cli('init','init');two=cli('init-again','init');assert one['status']==two['status']=='INSTALLATION_READY';assert one['installation']['installation_id']==two['installation']['installation_id']
 start=cli('start','start');status=cli('status','status');assert status['service']['alive'] and status['service']['process']=='RUNNING'
 def state():return {p.relative_to(out/'state').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (out/'state').rglob('*') if p.is_file()}
 before=state();doctor=cli('doctor','doctor');assert before==state(),'doctor mutated state'
 p=subprocess.Popen([sys.executable,'-B','scripts/run_unified_market_evidence_mcp.py','--home',str(out/'home'),'--state-root',str(out/'state'),'--service-url',f'http://127.0.0.1:{port}'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',bufsize=1)
 q=queue.Queue();raw=[];errors=[]
 def read():
  for line in p.stdout:raw.append(line);q.put(json.loads(line))
 t=threading.Thread(target=read,daemon=True);t.start()
 def err():
  for line in p.stderr:errors.append(line)
 threading.Thread(target=err,daemon=True).start()
 def send(d):p.stdin.write(json.dumps(d)+'\n');p.stdin.flush()
 def response(i):
  while True:
   d=q.get(timeout=45)
   if d.get('id')==i:return d
 send(dict(jsonrpc='2.0',id=1,method='initialize',params=dict(protocolVersion='2024-11-05',capabilities={},clientInfo=dict(name='A3-311-compatibility',version='1'))));initialize=response(1);assert 'result' in initialize
 send(dict(jsonrpc='2.0',method='notifications/initialized'));send(dict(jsonrpc='2.0',id=2,method='tools/list',params={}));listing=response(2);p.stdin.close();p.wait(timeout=45)
 names=sorted(x['name'] for x in listing['result']['tools']);assert names==sorted(['market_describe_capabilities','market_export_ai_handoff','market_fetch_evidence','market_preview_request','market_read_result','market_validate_request']);assert p.returncode==0
 save('mcp',dict(initialize=initialize,listing=listing,raw=raw,stderr=errors,exit_code=p.returncode));result.update(status='PASS',installation_id=one['installation']['installation_id'],tools=names,doctor_read_only=True,python=sys.version,scope='Noncanonical Python 3.11 source/runtime compatibility; not Native bootstrap or canonical release gate')
finally:
 stop=cli('stop','stop');events=[json.loads(x) for x in (out/'guard.jsonl').read_text().splitlines()] if (out/'guard.jsonl').exists() else [];result.update(sequence=sequence,guard_denials=[x for x in events if x.get('event')=='denied' or 'blocked' in x]);save('result',result)
assert result['status']=='PASS' and not result['guard_denials']
print('Python 3.11 source lifecycle and exact-six PASS; zero guard denials')
