import pathlib,json
R=pathlib.Path(r'C:\twmarket_temp\l6-a6');old=pathlib.Path(r'C:\twmarket_temp\l6-a5')
for d in ['ci','expanded','focused','temp']:(R/d).mkdir(exist_ok=True)
guard=(old/'ci/guard.py').read_text().replace(str(old),str(R))
# Explicitly deny even read access to the owner production HOME.
guard=guard.replace("value=os.path.normcase(os.path.abspath(os.fsdecode(path)))", "value=os.path.normcase(os.path.abspath(os.fsdecode(path)))\n    owner=os.path.normcase(str(Path(os.environ['USERPROFILE'])/'AppData/Local/TW-Market'))\n    if value==owner or value.startswith(owner+os.sep):reject('OWNER_PRODUCTION_STATE_ACCESS',value)")
(R/'ci/guard.py').write_bytes(guard.encode())
wrapper=(old/'run_default_ci.py').read_text().replace(str(old),str(R)).replace('C:/twmarket_temp/l6-a5','C:/twmarket_temp/l6-a6')
(R/'run_default_ci.py').write_bytes(wrapper.encode())
selected=json.loads((old/'final-run/focused/selected-tests.json').read_text())
(R/'expanded/selected-tests.json').write_bytes(json.dumps(selected,indent=2).encode())
code='''import os,pathlib,runpy,sys,json
r=pathlib.Path(r'C:\\twmarket_temp\\l6-a6');out=r/'expanded'
os.environ.update(TEMP=str(out/'temp'),TMP=str(out/'temp'),LOCALAPPDATA=str(out/'user-local'),TW_MARKET_HOME=str(out/'home'),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
os.environ['PATH']=os.pathsep.join([str(pathlib.Path(sys.executable).parent),r'C:\\Windows\\System32',r'C:\\Windows',r'C:\\Program Files\\Git\\cmd'])
for p in [out/'temp',out/'user-local']:p.mkdir(exist_ok=True)
runpy.run_path(str(r/'ci/guard.py'),run_name='_review_guard')
sys.path.insert(0,str(pathlib.Path.cwd()))
import pytest
tests=json.loads((out/'selected-tests.json').read_text())
sys.exit(pytest.main(['-q','-p','no:cacheprovider','--basetemp='+str(out/'pytest-temp'),'--junitxml='+str(out/'report.xml'),*tests]))
'''
(R/'run_expanded.py').write_bytes(code.encode())
print('bounded A6 wrappers ready')
