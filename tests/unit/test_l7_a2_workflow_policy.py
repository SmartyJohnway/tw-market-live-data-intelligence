from pathlib import Path
import shutil
import pytest
import yaml
from scripts.validate_l7_a2_workflow_policy import ROOT, validate, smoke_job_eligible


def test_committed_workflow_trigger_contract():
    assert validate()['status']=='PASS'


@pytest.mark.parametrize('action',['opened','synchronize','reopened','labeled'])
def test_actual_windows_job_label_eligibility(action):
    workflow=yaml.load((ROOT/'.github/workflows/windows-compatibility-smoke.yml').read_text(),Loader=yaml.BaseLoader)
    assert smoke_job_eligible(workflow,'pull_request',('windows-smoke',),action)
    assert not smoke_job_eligible(workflow,'pull_request',(),action)
    assert not smoke_job_eligible(workflow,'pull_request',('unrelated',),action)
    assert smoke_job_eligible(workflow,'workflow_dispatch')
    assert not smoke_job_eligible(workflow,'push',('windows-smoke',),action)


@pytest.mark.parametrize('mutation',['published','write','missing-sync','always-run','extra-job','publish-action','git-tag','mutable-action'])
def test_policy_rejects_regressions(tmp_path,mutation):
    destination=tmp_path/'.github/workflows'
    destination.mkdir(parents=True)
    for name in ('release-validation','windows-compatibility-smoke'):
        shutil.copyfile(ROOT/'.github/workflows'/(name+'.yml'),destination/(name+'.yml'))
    path=destination/'windows-compatibility-smoke.yml'
    data=yaml.load(path.read_text(),Loader=yaml.BaseLoader)
    if mutation=='published':data['on']['release']={'types':['published']}
    if mutation=='write':data['permissions']['contents']='write'
    if mutation=='missing-sync':data['on']['pull_request']['types'].remove('synchronize')
    if mutation=='always-run':data['jobs']['validation']['if']='true'
    if mutation=='extra-job':data['jobs']['unguarded']={'runs-on':'windows-latest','steps':[]}
    if mutation=='publish-action':data['jobs']['validation']['steps'].append({'uses':'softprops/action-gh-release@v2'})
    if mutation=='git-tag':data['jobs']['validation']['steps'].append({'run':'git tag release'})
    if mutation=='mutable-action':data['jobs']['validation']['steps'][0]['uses']='actions/setup-python@v5'
    path.write_text(yaml.safe_dump(data,sort_keys=False))
    with pytest.raises(AssertionError):validate(tmp_path)
