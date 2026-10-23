import hashlib,json,os,pathlib,platform,runpy,subprocess,sys
inputs=pathlib.Path(__file__).parent;out=inputs.parent/'output'
def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))
def save(name,data):(out/(name+'.json')).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
fresh=load(out/'fresh-environment.json');package=load(out/'package-before-bootstrap.json');bundle=pathlib.Path(package['bundle'])
assert not fresh['twmarket_home_existed'] and not fresh['python_on_path'] and not fresh['guest_prerequisite_existed']
assert not package['venv_existed_before'] and not package['git_existed']
authority=load(inputs/'acceptance-source.json');manifest=load(bundle/'distribution-manifest.json')
assert manifest['source_commit']==authority['commit'] and manifest['source_tree']==authority['tree']
home=pathlib.Path(os.environ['LOCALAPPDATA'])/'TW-Market';assert not home.exists()
os.environ.update(A5_OUTPUT=str(out),A5_APP_ROOT=str(bundle/'app'),TEMP=r'C:\A5\Temp',TMP=r'C:\A5\Temp',PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
runpy.run_path(str(inputs/'runtime_guard.py'),run_name='_a5_guard')
env=dict(os.environ)
for key in list(env):
    if key.startswith(('TW_MARKET_','UNIFIED_MARKET_','M8R_','PYTHONHOME','PYTHONPATH')):env.pop(key)
py=bundle/'runtime/venv/Scripts/python.exe';launch=bundle/'bootstrap/launch.py';records=[]
def fingerprint(root):return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob('*')) if p.is_file()} if root.exists() else {}
def stable_home():return {k:v for k,v in fingerprint(home).items() if not k.startswith('logs/')}
def command(name,*args,expected=0):
    p=subprocess.run([str(py),'-B',str(launch),'market',name,*args,'--json'],env=dict(env,A5_READ_ONLY='1' if name in {'status','doctor'} else '0'),cwd=bundle,capture_output=True,text=True,encoding='utf-8',timeout=120)
    d={'command':name,'returncode':p.returncode,'result':json.loads(p.stdout),'stderr':p.stderr};records.append(d);save('command-'+str(len(records)),d);assert p.returncode==expected,d;return d
app_expected={m['relative_path'].removeprefix('app/'):m['sha256'] for m in manifest['members'] if m['relative_path'].startswith('app/')}
assert fingerprint(bundle/'app')==app_expected
for name in ['status','doctor','start']:
    d=command(name,expected=1 if name=='start' else 0);assert d['result']['status']=='INSTALLATION_NOT_INITIALIZED';assert not home.exists()
init=command('init');before=stable_home();command('init');assert stable_home()==before
meta=load(home/'meta/installation.json');state=pathlib.Path(meta['state_root']);sm=state/'security-master'
assert state==home/'state' and not list(sm.iterdir())
before=stable_home();command('status');command('doctor');assert stable_home()==before
sys.path.insert(0,str(inputs));from raw_stdio import probe
def lifecycle():
    command('start','--port','18453')
    try:
        status=command('status','--port','18453');before=stable_home();doctor=command('doctor','--port','18453');assert stable_home()==before
        mcp=probe(py,['-B',launch,'mcp','--service-url','http://127.0.0.1:18453'],env,bundle)
        return {'status':status,'doctor':doctor,'mcp':mcp}
    finally:command('stop','--port','18453')
uninitialized=lifecycle();assert uninitialized['status']['result']['identity']['status']=='NOT_INITIALIZED' and not list(sm.iterdir())
sys.path.insert(0,str(bundle/'app'));os.chdir(bundle/'app')
from scripts.m8r_08g_security_master_releases import build_candidate_release,qualify_candidate_release,activate_qualified_release,load_active_identity_service
record={'canonical_target_id':'TWSE:2330','identity':{'security_code':'2330','isin':'TW0002330008'},'classification':{'market':'TWSE','instrument_type':'common_share'},'lifecycle':{'state':'listed','resolution_status':'resolved','basis_event_ids':[],'events':[]},'execution_eligibility':{'status':'allowed','reason_codes':[]}}
provenance={'source_type':'test','snapshot_id':'a5-offline-accepted-fixture','source_content_hashes':{'fixture':'a'*64},'producer_skill':{'name':'test','skill_version':'1','skill_contract_hash':'b'*64}}
rid='security-master-20261023T000000Z';build_candidate_release(root=sm,release_id=rid,records=[record],source_provenance=provenance)
qualified,report=qualify_candidate_release(root=sm,release_id=rid);assert qualified is not None and report['status']=='PASS'
pointer=activate_qualified_release(root=sm,release_id=rid);load_active_identity_service(root=sm)
sm_before=fingerprint(sm);active=lifecycle();assert active['status']['result']['identity']['status']=='ACTIVE' and fingerprint(sm)==sm_before
assert fingerprint(bundle/'app')==app_expected and not (out/'guard-blocks.jsonl').exists()
host=load(inputs/'host-identity.json');assert fresh['sid']!=host['sid'] and fresh['profile'].lower()!=host['profile'].lower() and fresh['computer'].lower()!=host['computer'].lower()
save('p2_distinct_user',{'status':'PASS','guest':fresh,'host_identity_comparison':host,'distinct_sid':True,'distinct_profile':True,'no_inherited_HOME_or_runtime':True,'home':str(home),'state_root':str(state),'installation_id':meta['installation_id'],'no_host_profile_mapping':True,'no_host_runtime_or_pid_authority':True})
save('p3_fresh_win11',{'status':'PASS','fresh_environment':fresh,'package':package,'source_commit':manifest['source_commit'],'source_tree':manifest['source_tree'],'python':sys.version,'python_base_prefix':sys.base_prefix,'python_executable':sys.executable,'architecture':platform.machine(),'installation_id':meta['installation_id'],'home':str(home),'state_root':str(state),'preinit_read_only':True,'init_idempotent':True,'lifecycle':records,'before_SM_lifecycle':uninitialized,'after_SM_lifecycle':active,'explicit_security_master':{'fixture_authority':'tests/unit/test_m8r_08g_identity_service_and_releases.py::test_candidate_passes_then_activates','qualification':report,'pointer':pointer,'canonical_root':str(sm),'live_fetches':0,'state_hashes':sm_before},'app_root_unchanged':True,'app_hashes':app_expected,'networking':'disabled','network_guard':'Python audit/stat hooks propagated to Python descendants','provider_attempts':0,'guard_rejections':0,'integration_independence':'guest has only staged package and official CPython prerequisite; no host profile/checkout/venv/Agent/tunnel mapping'})
save('completed',{'P2':'PASS','P3':'PASS','source_commit':manifest['source_commit'],'source_tree':manifest['source_tree']})
