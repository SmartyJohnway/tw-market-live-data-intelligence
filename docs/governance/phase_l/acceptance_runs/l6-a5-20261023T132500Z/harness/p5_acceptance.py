import hashlib,json,os,pathlib,subprocess,sys
r=pathlib.Path(r'C:\twmarket_temp\l6-a5\final-run');sys.path.insert(0,str(r));import host_acceptance as h
h.OUT=r/'evidence-p5';h.OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(r/'sandbox/input'));from raw_stdio import probe
async def mcp(bundle,home,port):
    return probe(bundle/'runtime/venv/Scripts/python.exe',['-B',bundle/'bootstrap/launch.py','mcp','--home',home,'--service-url',f'http://127.0.0.1:{port}'],dict(h.env,TW_MARKET_HOME=str(home)),bundle)
h.mcp=mcp
archive=pathlib.Path(r'C:\twmarket_temp\l6-a5\final-run\historical-cache\TW-Market-1.0.0-windows-x64.zip')
assert h.sha(archive)=='14dfd36c61ccf173999836932031304e151d93e9b342482bf3cd3d467b48ff7d'
old=h.extract(archive,r/'historical/accepted-a3');h.bootstrap(old)
manifest=json.loads((old/'distribution-manifest.json').read_text())
assert manifest['source_commit']=='0c1850ac23db5a9a4e25a5196ca62dedf17ece2a'
home=r/'installations/p5-home';assert h.command(old,'init',home)['returncode']==0
seed=subprocess.run([str(old/'runtime/venv/Scripts/python.exe'),'-B',str(r/'p5_seed.py'),'--bundle',str(old),'--home',str(home)],env=h.env,capture_output=True,text=True,encoding='utf-8',timeout=120)
assert seed.returncode==0,seed.stderr
metadata=json.loads((home/'meta/installation.json').read_text());state=pathlib.Path(metadata['state_root'])
durable=h.inventory(state);meta=h.sha(home/'meta/installation.json');settings=h.sha(home/'config/settings.json')
old_result=h.lifecycle(old,home,18455)
paths=json.loads((r/'evidence-host-run4/packaged-runtime-paths.json').read_text(encoding='utf-8'));new=pathlib.Path(paths['bundle'])
app_before=h.inventory(new/'app')
upgraded=h.lifecycle(new,home,18455)
assert h.inventory(new/'app')==app_before and h.inventory(state)==durable and h.sha(home/'meta/installation.json')==meta and h.sha(home/'config/settings.json')==settings
rolled_back=h.lifecycle(old,home,18455)
assert h.inventory(state)==durable and h.sha(home/'meta/installation.json')==meta and h.sha(home/'config/settings.json')==settings
out={'status':'PASS','compatibility':'SUPPORTED_NO_MIGRATION_REQUIRED','old_source_commit':manifest['source_commit'],'old_source_tree':manifest['source_tree'],'old_zip_sha256':h.sha(archive),'new_source_commit':json.loads((new/'distribution-manifest.json').read_text())['source_commit'],'installation_id':metadata['installation_id'],'installation_schema_version':metadata['installation_schema_version'],'metadata_sha256':meta,'settings_sha256':settings,'durable_hashes':durable,'old_lifecycle':old_result,'upgrade_lifecycle':upgraded,'rollback_lifecycle':rolled_back,'hidden_refreshes':0,'migration_executed':False}
(r/'p5_upgrade_rollback.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
print('P5 PASS')
