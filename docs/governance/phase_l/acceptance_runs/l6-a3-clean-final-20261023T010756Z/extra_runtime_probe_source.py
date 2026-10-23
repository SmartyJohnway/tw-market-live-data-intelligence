import sys,os,json,shutil,runpy
from pathlib import Path
app=Path('C:\\twmarket_temp\\acceptance\\a3-accepted-20261023\\Location A With Spaces 非ASCII\\TW-Market-1.0.0-windows-x64\\app')
sys.path.insert(0,str(app))
import server.main
from scripts.product_version import product_version
from scripts.tw_market_installation import resolve_installation
from scripts.m8r_06_security_master_candidate_paths import temp_security_master_root,retained_source_bundle_dir
from scripts.m8r_08g_security_master_releases import _commit
from scripts.m8r_03d_f1_security_master_snapshot_exporter import compute_skill_contract_hash
runpy.run_path(str(app/'scripts/m8r_06_01b_materialize_production_inputs.py'),run_name='_resource_import_probe')
inst=resolve_installation()
origins={n:m.__file__ for n,m in sys.modules.copy().items() if n.startswith(('scripts.','server.')) and getattr(m,'__file__',None)}
assert all(Path(p).is_relative_to(app) for p in origins.values())
assert shutil.which('git') is None
assert not (app.parent/'.git').exists()
assert all('l6-a3-clean' not in p.lower() and 'tools-venv' not in p.lower() for p in sys.path)
staging=temp_security_master_root(app,installation=inst)
retained=retained_source_bundle_dir(inst.security_master_root,'m8r06-01b-20261023T000000Z')
assert staging.is_relative_to(Path(os.environ['TEMP']))
assert retained.is_relative_to(inst.state_root)
print(json.dumps({'status':'PASS','sys_path':sys.path,'sys_executable':sys.executable,'git_executable':shutil.which('git'),'APP_ROOT':str(app),'HOME':str(inst.home),'STATE_ROOT':str(inst.state_root),'TEMP':os.environ['TEMP'],'TMP':os.environ['TMP'],'SM_staging':str(staging),'SM_retained_provenance':str(retained),'source_commit':_commit(),'version':product_version(),'skill_contract_hash':compute_skill_contract_hash(),'module_origins':origins},sort_keys=True))
