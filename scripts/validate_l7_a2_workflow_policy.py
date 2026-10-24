"""Deterministic pre-publication/opt-in trigger contract checks."""
from pathlib import Path
import json
import re
import yaml

ROOT=Path(__file__).resolve().parents[1]
SMOKE_IF="github.event_name == 'workflow_dispatch' || contains(github.event.pull_request.labels.*.name, 'windows-smoke')"


def smoke_job_eligible(workflow, event_name, labels=(), action=None):
    assert workflow['jobs']['validation']['if']==SMOKE_IF
    if event_name=='workflow_dispatch':return 'workflow_dispatch' in workflow['on']
    if event_name!='pull_request':return False
    return action in workflow['on']['pull_request']['types'] and 'windows-smoke' in labels


def validate(root=ROOT):
    for name in ('release-validation','windows-compatibility-smoke'):
        path=root/'.github/workflows'/(name+'.yml')
        workflow=yaml.load(path.read_text(encoding='utf-8'),Loader=yaml.BaseLoader)
        assert workflow['permissions']=={'contents':'read'}
        trigger=workflow['on']
        assert 'release' not in trigger
        assert 'workflow_dispatch' in trigger
        if name=='windows-compatibility-smoke':
            assert set(workflow['jobs'])=={'validation'}, 'unguarded extra Windows job'
            assert set(trigger)=={'workflow_dispatch','pull_request'}
            assert trigger['pull_request']['types']==['opened','synchronize','reopened','labeled']
            assert workflow['jobs']['validation']['if']==SMOKE_IF
            for action in ('opened','synchronize','reopened','labeled'):
                assert not smoke_job_eligible(workflow,'pull_request',(),action)
                assert smoke_job_eligible(workflow,'pull_request',('windows-smoke',),action)
            assert smoke_job_eligible(workflow,'workflow_dispatch')
        else:
            assert set(trigger)=={'workflow_dispatch'}
            assert set(workflow['jobs'])=={'validation','docker-validation'}
            assert 'accept_l7_a2_docker.py' in path.read_text()
        text=path.read_text()
        assert 'run_l7_a2_release_validation.py' in text
        assert '--gate' in text
        assert 'windows-latest' in text
        assert 'GITHUB_SHA' in text or 'SOURCE_SHA' in text
        for job in workflow['jobs'].values():
            assert job.get('permissions',{'contents':'read'})=={'contents':'read'}
            for step in job.get('steps',[]):
                if 'uses' in step:
                    assert step['uses'] in {'actions/checkout@v4','actions/setup-python@v5'}, 'unapproved publication-capable action'
        assert not re.search(r'\bgit\s+(?:-\S+\s+)*tag\b|\b(?:gh|hub)\s+release\b',text)
        for forbidden in ('release: published','gh release','docker push','packages: write','contents: write','pull_request_target','secrets.'):
            assert forbidden not in text, forbidden
    return {'status':'PASS','unlabeled_pr_expensive_job':False,'labeled_pr_synchronize_eligible':True,'labeled_pr_reopen_eligible':True,'manual_dispatch_eligible':True,'pre_publication':True,'genuine_windows11_claim':False}


if __name__=='__main__':
    print(json.dumps(validate(),indent=2))
