import os,pathlib,sys,subprocess,json,runpy
R=pathlib.Path(r'C:\twmarket_temp\l6-a6');P=R/'repo';E=P/'docs/governance/phase_l/acceptance_runs/l6-a6-20261023T141800Z'
env=dict(os.environ,TEMP=str(R/'temp'),TMP=str(R/'temp'),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1',TW_MARKET_HOME=str(R/'validators-home'),LOCALAPPDATA=str(R/'validators-local'))
scripts=['validate_phase_h_v3_contracts.py','validate_portable_catalog_sync.py','validate_runtime_skill_guide_sync.py','validate_product_version_consistency.py','validate_v1_front_door.py','validate_source_registry.py','validate_release_hygiene.py','governance_forbidden_path_guard.py']
results=[]
for s in scripts:
    p=subprocess.run([sys.executable,'-B','scripts/'+s],cwd=P,env=env,capture_output=True,text=True,encoding='utf-8',timeout=90);results.append(dict(script=s,returncode=p.returncode,stdout=p.stdout,stderr=p.stderr))
(E/'required_validators.json').write_bytes((json.dumps(results,ensure_ascii=False,indent=2)+'\n').encode());assert all(x['returncode']==0 for x in results),[x for x in results if x['returncode']]
p=subprocess.run([sys.executable,'-X','pycache_prefix='+str(R/'compile-cache'),'-m','compileall','-q','scripts','server','packaging_native','tests/unit'],cwd=P,env=env,capture_output=True,text=True,encoding='utf-8',timeout=120)
(E/'compile_static.json').write_bytes((json.dumps(dict(returncode=p.returncode,stdout=p.stdout,stderr=p.stderr),indent=2)+'\n').encode());assert p.returncode==0
print('required validators and compile/static PASS')
