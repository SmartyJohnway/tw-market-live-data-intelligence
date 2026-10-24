import hashlib,json,os,sys
from pathlib import Path

ROOT=Path(r'C:\twmarket_temp\l7-a2\repo')
OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=False)
os.chdir(ROOT);sys.path.insert(0,str(ROOT))
for name in ('home','state','local','temp'):(OUT/name).mkdir()
os.environ.update(TW_MARKET_CI_NODE=r'C:\Program Files\nodejs\node.exe',TW_MARKET_CI_BOUND=r'C:\twmarket_temp\l7-a2',TW_MARKET_CI_GUARD_LOG=str(OUT/'guard.jsonl'),TW_MARKET_HOME=str(OUT/'home'),TW_MARKET_STATE_ROOT=str(OUT/'state'),LOCALAPPDATA=str(OUT/'local'),TEMP=str(OUT/'temp'),TMP=str(OUT/'temp'),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
for key in list(os.environ):
    if key.lower() in ('http_proxy','https_proxy','all_proxy'):os.environ.pop(key)
from scripts.deterministic_ci_guard import install
install()
import fastapi,starlette,pytest
import importlib.metadata as metadata
from server.main import app
from server.local_control_plane_boundary import POST_ROUTE_CLASSIFICATIONS
from tests.post_route_surface import effective_post_paths,schema_post_paths_with_visibility_guard
schema=schema_post_paths_with_visibility_guard(app);effective=effective_post_paths(app);classified=set(POST_ROUTE_CLASSIFICATIONS)
def save(name,value):(OUT/(name+'.json')).write_bytes((json.dumps(value,indent=2,sort_keys=True)+'\n').encode())
save('environment',{'python':sys.version,'executable':sys.executable,'fastapi':fastapi.__version__,'starlette':starlette.__version__,'versions':sorted([{'name':d.metadata['Name'],'version':d.version} for d in metadata.distributions()],key=lambda d:d['name'].lower())})
save('surface',{'effective_POST_count':len(effective),'schema_POST_count':len(schema),'classification_count':len(classified),'effective_POST_paths':sorted(effective),'schema_POST_paths':sorted(schema),'classified_paths':sorted(classified),'missing_classifications':sorted(effective-classified),'stale_classifications':sorted(classified-effective),'exact_equality':effective==schema==classified,'included_unified_POST_paths':sorted(p for p in effective if p.startswith('/api/unified/')),'legacy_flat_POST_paths':sorted(r.path for r in app.routes if 'POST' in getattr(r,'methods',set()))})
code=pytest.main(['-q','-p','no:cacheprovider','--basetemp='+str(OUT/'pytest-temp'),'--junitxml='+str(OUT/'report.xml'),'tests/unit/test_phase_l_l4_a4_control_plane_boundary.py','tests/unit/test_l7_a1_deterministic_ci.py','tests/unit/test_post_route_surface_compatibility.py'])
events=[json.loads(s) for s in (OUT/'guard.jsonl').read_text().splitlines()]
save('result',{'pytest_exit_code':int(code),'guard_denials':[e for e in events if e['event']=='denied'],'network_scope':'Python and inherited Python/Node; no OS firewall claim','boundary':str(Path(r'C:\twmarket_temp\l7-a2'))})
raise SystemExit(code or bool([e for e in events if e['event']=='denied']))
