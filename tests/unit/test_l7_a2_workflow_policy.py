from pathlib import Path
import shutil
import pytest
import yaml
from scripts.validate_l7_a2_workflow_policy import ROOT, validate


def test_committed_workflow_trigger_contract():
    assert validate()['status']=='PASS'


@pytest.mark.parametrize('mutation',['published','write','missing-sync','always-run'])
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
    path.write_text(yaml.safe_dump(data,sort_keys=False))
    with pytest.raises(AssertionError):validate(tmp_path)
