"""Execute the versioned release-blocking contract with process containment."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output-root',type=Path,required=True)
    args=p.parse_args(argv)
    if args.output_root.drive.upper()=='D:':raise ValueError('forbidden CI output drive')
    # Filter forbidden discovery roots lexically before any prerequisite lookup.
    os.environ['PATH']=os.pathsep.join(x for x in os.environ.get('PATH','').split(os.pathsep) if Path(x.strip('"')).drive.upper()!='D:')
    sys.path[:]=[x for x in sys.path if Path(x).drive.upper()!='D:']
    out=args.output_root.resolve()
    if out==ROOT or ROOT in out.parents:raise ValueError('CI output root must be outside APP_ROOT')
    bound=ROOT.parent
    if not out.is_relative_to(bound):raise ValueError('CI output must be under the isolated workspace parent')
    if out.exists():raise ValueError('CI output root must be fresh')
    out.mkdir(parents=True)
    contract=json.loads((ROOT/'config/release_blocking_ci.v1.json').read_text(encoding='utf-8'))
    for name in ['home','state','temp','local']:(out/name).mkdir()
    node=os.environ.get('TW_MARKET_CI_NODE') or shutil.which('node')
    if not node:raise RuntimeError('release-blocking-ci requires existing Node; installation is separate prerequisite setup')
    os.environ.update(TW_MARKET_CI_NODE=str(node),TW_MARKET_CI_BOUND=str(bound),TW_MARKET_CI_GUARD_LOG=str(out/'guard.jsonl'),TW_MARKET_HOME=str(out/'home'),TW_MARKET_STATE_ROOT=str(out/'state'),LOCALAPPDATA=str(out/'local'),TEMP=str(out/'temp'),TMP=str(out/'temp'),PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
    for name in ['TW_MARKET_SECURITY_MASTER_ROOT','TW_MARKET_WATCHLIST_ROOT','M8R_06_03_CONTROL_ROOT','TW_MARKET_OPERATIONAL_EVENT_PATH','PYTEST_ADDOPTS','A6_SESSION_ROOT']:
        os.environ.pop(name,None)
    for key in list(os.environ):
        if key.lower() in {'http_proxy','https_proxy','all_proxy'}:os.environ.pop(key)
    import tempfile
    tempfile.tempdir=str(out/'temp')
    from scripts.deterministic_ci_guard import install
    install()
    import pytest
    historical=contract['historical_diagnostics']
    class Members:
        def __init__(self):
            self.historical=[]
            self.deselected=[]
            self.skipped=[]
            self.unexpected_skips=[]
        def pytest_collection_modifyitems(self,session,config,items):
            excluded=[x for x in items if x.nodeid in historical]
            items[:]=[x for x in items if x.nodeid not in historical]
            self.historical=[x.nodeid for x in excluded]
            config.hook.pytest_deselected(items=excluded)
        def pytest_deselected(self,items):
            self.deselected.extend(x.nodeid for x in items)
        def pytest_collection_finish(self,session):
            (out/'members.json').write_text(json.dumps({'included_nodes':[x.nodeid for x in session.items],'excluded_historical_nodes':self.historical,'all_deselected_nodes':self.deselected,'marker_expression':contract['marker_expression']},indent=2)+'\n',encoding='utf-8')
        def pytest_runtest_logreport(self,report):
            if report.skipped:
                self.skipped.append(report.nodeid)
                allowed=contract['optional_historical_artifact_witnesses'].get(report.nodeid)
                if not allowed or allowed['expected_skip_reason'] not in str(report.longrepr) or hasattr(report,'wasxfail'):
                    self.unexpected_skips.append(report.nodeid)
    start=time.monotonic()
    members=Members()
    code=pytest.main(['-q','-p','no:cacheprovider','-m',contract['marker_expression'],'--basetemp='+str(out/'pytest-temp'),'--junitxml='+str(out/'report.xml'),*contract['pytest_paths']],plugins=[members])
    events=[json.loads(x) for x in (out/'guard.jsonl').read_text(encoding='utf-8').splitlines()]
    denied=[x for x in events if x['event']=='denied']
    result={'profile':'release-blocking-ci','profile_version':1,'pytest_exit_code':int(code),'guard_denials':denied,'skipped_nodes':members.skipped,'unexpected_skips':members.unexpected_skips,'elapsed_seconds':round(time.monotonic()-start,3),'status':'PASS' if code==0 and not denied and not members.unexpected_skips else 'FAIL','guard_events':len(events),'boundary':'Python audit and injected Python/Node child guards; local Git allowlist; no OS firewall claim'}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
