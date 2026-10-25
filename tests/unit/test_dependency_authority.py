from pathlib import Path
import copy
import hashlib
import json
import shutil

import pytest

from scripts.dependency_authority import ROOT, canonical, load_consumer, sbom, verify_artifacts
from scripts.validate_dependency_authority import validate


def test_repository_dependency_policy():
    assert validate()['status']=='PASS'


def test_sbom_stable_order_and_serialization():
    a=canonical(sbom())
    assert a==canonical(sbom())
    assert len(json.loads(a)['components'])>250


@pytest.mark.parametrize('mutation',['missing','wrong-bytes','extra'])
def test_replay_rejects_artifact_drift(tmp_path,mutation):
    b=b'wheel bytes';p=tmp_path/'sample.whl';p.write_bytes(b)
    rows=[{'wheel_filename':p.name,'sha256':hashlib.sha256(b).hexdigest()}]
    verify_artifacts(rows,tmp_path)
    if mutation=='missing':p.unlink()
    if mutation=='wrong-bytes':p.write_bytes(b+'tamper'.encode())
    if mutation=='extra':(tmp_path/'extra.whl').write_bytes(b)
    with pytest.raises(AssertionError):verify_artifacts(rows,tmp_path)


@pytest.mark.parametrize('mutation',['unhashed','mcp','yanked','duplicate','source'])
def test_consumer_lock_fails_closed(tmp_path,mutation):
    (tmp_path/'config').mkdir();(tmp_path/'packaging_native').mkdir()
    shutil.copyfile(ROOT/'config/dependency_authority.json',tmp_path/'config/dependency_authority.json')
    data=json.loads((ROOT/'packaging_native/wheelhouse-lock.json').read_bytes())
    rows=data['wheels']
    if mutation=='unhashed':rows[0]['sha256']=''
    if mutation=='mcp':next(r for r in rows if r['project']=='mcp')['version']='2.0.0'
    if mutation=='yanked':rows[0]['yanked']=True
    if mutation=='duplicate':rows.append(copy.deepcopy(rows[0]))
    if mutation=='source':rows[0]['release_metadata_url']='https://untrusted.example/package'
    (tmp_path/'packaging_native/wheelhouse-lock.json').write_text(json.dumps(data))
    with pytest.raises(AssertionError):load_consumer('native-windows',tmp_path)
