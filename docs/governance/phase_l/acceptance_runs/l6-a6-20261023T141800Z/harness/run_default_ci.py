"""Identical bounded wrapper used for exact base and candidate CI."""
import os,pathlib,runpy,sys
r=pathlib.Path(r'C:\twmarket_temp\l6-a6')
os.environ.update(TEMP=str(r/'ci/temp'),TMP=str(r/'ci/temp'),LOCALAPPDATA=str(r/'ci/user-local'),TW_MARKET_HOME=str(r/'ci/home'),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTEST_ADDOPTS='--basetemp=C:/twmarket_temp/l6-a6/ci/pytest-temp --junitxml=C:/twmarket_temp/l6-a6/ci/report.xml')
for path in [r/'ci/temp',r/'ci/user-local']:path.mkdir(parents=True,exist_ok=True)
os.environ['PATH']=os.pathsep.join([str(pathlib.Path(sys.executable).parent),r'C:\Windows\System32',r'C:\Windows',r'C:\Program Files\Git\cmd'])
sys.path.insert(0,str(pathlib.Path.cwd()))
runpy.run_path(str(r/'ci/guard.py'),run_name='_a5_ci_guard')
sys.argv=['scripts/run_test_profile.py','default-ci','--json']
runpy.run_path('scripts/run_test_profile.py',run_name='__main__')
