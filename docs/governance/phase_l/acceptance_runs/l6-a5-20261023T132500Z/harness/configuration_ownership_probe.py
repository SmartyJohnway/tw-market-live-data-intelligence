import asyncio,hashlib,json,os,pathlib,sys,urllib.request
r=pathlib.Path(r'C:\twmarket_temp\l6-a5\final-run');sys.path.insert(0,str(r));import host_acceptance as h
h.OUT=r/'evidence-configuration';h.OUT.mkdir(exist_ok=True)
paths=json.loads((r/'evidence-host-run4/packaged-runtime-paths.json').read_text(encoding='utf-8'));bundle=pathlib.Path(paths['bundle'])
relocation=json.loads((r/'evidence-host-run4/p1_relocation.json').read_text(encoding='utf-8'))
h.env.update(A5_APP_ROOT=str(bundle/'app'),A5_FORBIDDEN_READ_PREFIX=relocation['app_a'])
sys.path.insert(0,str(r/'sandbox/input'));from raw_stdio import probe
async def mcp(bundle,home,port):return probe(bundle/'runtime/venv/Scripts/python.exe',['-B',bundle/'bootstrap/launch.py','mcp','--home',home,'--service-url',f'http://127.0.0.1:{port}'],dict(h.env,TW_MARKET_HOME=str(home)),bundle)
h.mcp=mcp
app_before=h.inventory(bundle/'app');home=r/'installations/configuration-home'
assert h.command(bundle,'init',home)['returncode']==0
meta=h.sha(home/'meta/installation.json');p=home/'config/settings.json';p.write_text(json.dumps({'schema_version':1,'service':{'host':'127.0.0.1','port':18461}}),encoding='utf-8')
cases=[]
def status(label,args,extra_env,expected_host,expected_port,origins):
    import subprocess
    env=dict(h.env,**extra_env,A5_READ_ONLY='1')
    proc=subprocess.run([str(bundle/'runtime/venv/Scripts/python.exe'),'-B',str(bundle/'bootstrap/launch.py'),'market','status',*args,'--json'],env=env,cwd=bundle,capture_output=True,text=True,encoding='utf-8',timeout=90)
    assert proc.returncode==0,proc.stderr
    d=json.loads(proc.stdout);i=d['installation'];assert i['effective_service_host']==expected_host and i['effective_service_port']==expected_port
    assert i['home']==str(r/'installations/not-initialized-default' if label=='product-default' else home)
    assert i['diagnostics']['settings_origins']==origins
    cases.append({'label':label,'result':d,'stderr':proc.stderr})
status('settings',['--home',str(home)],{},'127.0.0.1',18461,{'host':'settings','port':'settings'})
status('environment',[],{'TW_MARKET_HOME':str(home),'TW_MARKET_HOST':'localhost','TW_MARKET_PORT':'18462'},'localhost',18462,{'host':'env','port':'env'})
status('CLI',['--home',str(home),'--host','::1','--port','18463'],{'TW_MARKET_HOME':str(r/'installations/unselected-home'),'TW_MARKET_HOST':'localhost','TW_MARKET_PORT':'18462'},'::1',18463,{'host':'cli','port':'cli'})
status('product-default',['--home',str(r/'installations/not-initialized-default')],{},'127.0.0.1',8000,{'host':'product_default','port':'product_default'})
conflict=h.command(bundle,'status',home,'--state-root',str(r/'installations/forbidden-conflicting-state'))
assert conflict['returncode']!=0 and 'STATE_ROOT_CONFLICT' in json.dumps(conflict)
assert not (r/'installations/forbidden-conflicting-state').exists() and h.sha(home/'meta/installation.json')==meta
assert h.command(bundle,'start',home,'--port','18464')['returncode']==0
owner=pathlib.Path(h.env['TEMP'])/'TW-Market'/json.loads((home/'meta/installation.json').read_text())['installation_id']/'runtime/service-18464.json'
original=owner.read_bytes();ownership=[]
try:
    for key,value in [('installation_id','00000000-0000-4000-8000-000000000000'),('process_start_token','stale-token'),('executable',str(r/'not-the-service.exe'))]:
        d=json.loads(original);d[key]=value;owner.write_text(json.dumps(d),encoding='utf-8')
        rejected=h.command(bundle,'stop',home,'--port','18464');assert rejected['returncode']!=0 and 'STALE_PROCESS_OWNERSHIP' in json.dumps(rejected)
        with urllib.request.urlopen('http://127.0.0.1:18464/api/health',timeout=2) as response:assert response.status==200
        ownership.append({'mutation':key,'result':rejected,'owned_process_still_alive':True});owner.write_bytes(original)
finally:
    owner.write_bytes(original);assert h.command(bundle,'stop',home,'--port','18464')['returncode']==0
strict_relocation=h.lifecycle(bundle,pathlib.Path(paths['home']),18451)
assert h.inventory(bundle/'app')==app_before and h.sha(home/'meta/installation.json')==meta
(h.OUT/'configuration_precedence.json').write_text(json.dumps({'status':'PASS','cases':cases,'home_CLI_over_ENV':True,'ENV_home_selection':True,'Windows_default_HOME_evidence':'Sandbox p2/p3 actual profile; no host production HOME used','state_root_conflict':conflict,'installation_id_stable_across_ports':True},indent=2,ensure_ascii=False),encoding='utf-8')
(h.OUT/'lifecycle_ownership.json').write_text(json.dumps({'status':'PASS','cases':ownership,'owned_final_stop':True,'app_root_unchanged':True,'strict_relocated_runtime':strict_relocation,'old_app_root_access_guard':'old App A path rejected before Python filesystem access; no rejection occurred'},indent=2,ensure_ascii=False),encoding='utf-8')
print('configuration / ownership / strict relocated Native PASS')
