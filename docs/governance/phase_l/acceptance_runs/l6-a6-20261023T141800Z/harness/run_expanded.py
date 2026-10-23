import os,pathlib,runpy,sys,json
r=pathlib.Path(r'C:\twmarket_temp\l6-a6');out=r/'expanded'
os.environ.update(TEMP=str(out/'temp'),TMP=str(out/'temp'),LOCALAPPDATA=str(out/'user-local'),TW_MARKET_HOME=str(out/'home'),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
os.environ['PATH']=os.pathsep.join([str(pathlib.Path(sys.executable).parent),r'C:\Windows\System32',r'C:\Windows',r'C:\Program Files\Git\cmd'])
for p in [out/'temp',out/'user-local']:p.mkdir(exist_ok=True)
runpy.run_path(str(r/'ci/guard.py'),run_name='_review_guard')
sys.path.insert(0,str(pathlib.Path.cwd()))
import pytest
tests=json.loads((out/'selected-tests.json').read_text())
sys.exit(pytest.main(['-q','-p','no:cacheprovider','--basetemp='+str(out/'pytest-temp'),'--junitxml='+str(out/'report.xml'),*tests]))
