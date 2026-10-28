"""Synthetic contract proofs only; no final artifact or live acceptance claim."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

import jsonschema
import pytest

from scripts import build_l7_rc_source_contract as s
from scripts import build_l7_publication_manifest as p
from scripts.validate_l7_release_artifact_hygiene import validate_artifact


def git(root,*args):
    return subprocess.check_output(['git','-c','core.hooksPath=NUL',*args],cwd=root,stderr=subprocess.STDOUT)


@pytest.fixture
def committed_source(tmp_path):
    root=tmp_path/'repo'; root.mkdir()
    for name in set(s.GOVERNED):
        dest=root/name; dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(s.ROOT/name,dest)
    git(root,'init','-q'); git(root,'add','.')
    git(root,'-c','user.name=Synthetic Fixture','-c','user.email=fixture@example.invalid','commit','-qm','synthetic source fixture')
    return root


@pytest.fixture
def contract(committed_source):
    return s.build_source_contract(committed_source)


@pytest.fixture
def synthetic(contract,tmp_path,committed_source):
    sc=deepcopy(contract); source=sc['source']; commit,tree=source['commit'],source['tree']
    assets=tmp_path/'synthetic-assets'; assets.mkdir()
    policies={r['role']:r for r in sc['artifact_set'] if r['classification']=='PUBLICATION_ASSET' and r['role']!='publication_manifest'}
    content={'native_zip':b'SYNTHETIC NATIVE ZIP TEST BYTES','mcpb':b'SYNTHETIC MCPB TEST BYTES',
             'first_party_sbom':(committed_source/'config/first_party_dependency_sbom.json').read_bytes()}
    for role,side in [('native_zip','native_checksum'),('mcpb','mcpb_checksum')]:
        content[side]=(s.sha(content[role])+'  '+policies[role]['filename']+'\n').encode()
    rows=[]
    for role,data in content.items():
        path=assets/policies[role]['filename']; path.write_bytes(data)
        rows.append({'role':role,'filename':path.name,'media_type':policies[role]['media_type'],
                     'bytes':len(data),'sha256':s.sha(data),'source_commit':commit,'source_tree':tree,'path':str(path)})
    common={'status':'PASS','source_commit':commit,'source_tree':tree,'evidence_sha256':s.sha(b'SYNTHETIC EVIDENCE ONLY'),
            'evidence_id':'SYNTHETIC_FIXTURE_NOT_ACCEPTANCE_AUTHORITY'}
    validation={
      'canonical_ci':{**common,'passed':1895,'failed':0,'contracted_skips':4,'deselected':20,'guard_events':386,'guard_denials':0,'unexpected_skips':0,'member_ledger_sha256':s.sha(b'SYNTHETIC')},
      'native':{**common,'os':'Windows 11','arch':'x64','native_zip_sha256':s.sha(content['native_zip'])},
      'docker':{**common,'platform':'linux/amd64','base_digest':'sha256:'+'a'*64,'image_identity':'sha256:'+'b'*64,'content_sha256':'c'*64,'rootfs_sha256':'d'*64,
                'runtime_configuration':{'entrypoint':['synthetic'],'command':[],'user':'synthetic','exposed_ports':[]},'reproducibility_boundary':p.BOUNDARY,'registry_publication':False},
      'compatibility':{**common,'public_contract_policy':'V1_RETAINED_WITH_CURRENT_V2_V3_COMPATIBILITY'},
      'bounded_live':{**common,'review_disposition':'SYNTHETIC_NO_LIVE_EXECUTION'},
      'artifact_hygiene':{**common,'blocking_count':0}}
    return sc,{'schema_version':'l7_artifact_binding.v1','source':source,'product_version':'1.5.0','artifacts':rows},\
           {'schema_version':'l7_validation_binding.v1','source':source,'product_version':'1.5.0','validation':validation},\
           committed_source/'docs/release/V1_5_0_RELEASE_NOTES_DRAFT.md'


def test_source_schema_and_exact_committed_identity(contract,committed_source):
    assert contract['source']['commit']==git(committed_source,'rev-parse','HEAD').decode().strip()
    assert contract['source']['tree']==git(committed_source,'rev-parse','HEAD^{tree}').decode().strip()
    s.validate(contract,json.loads((s.ROOT/s.SCHEMA).read_bytes()))
    assert not contract['stable_source_frozen'] and not contract['final_artifacts_frozen']


@pytest.mark.parametrize('target',['root','source','product','runtime_policy','dependency_authority'])
def test_source_schema_rejects_unknown_fields(contract,target):
    value=deepcopy(contract); (value if target=='root' else value[target])['unknown']='no'
    with pytest.raises(jsonschema.ValidationError): s.validate(value,json.loads((s.ROOT/s.SCHEMA).read_bytes()))


def test_source_builder_requires_clean_source(committed_source):
    (committed_source/'VERSION').write_text('1.5.1\n',encoding='utf-8')
    with pytest.raises(ValueError,match='clean and committed'): s.build_source_contract(committed_source)


def test_source_builder_rejects_untracked_source(committed_source):
    (committed_source/'unexpected.txt').write_text('uncommitted',encoding='utf-8')
    with pytest.raises(ValueError,match='clean and committed'): s.build_source_contract(committed_source)


def test_source_builder_requires_selected_version(committed_source):
    (committed_source/'VERSION').write_text('1.4.0\n',encoding='utf-8')
    git(committed_source,'add','VERSION')
    git(committed_source,'-c','user.name=Fixture','-c','user.email=fixture@example.invalid','commit','-qm','wrong version fixture')
    with pytest.raises(ValueError,match='VERSION'): s.build_source_contract(committed_source)


def test_external_output_rejects_repo_and_reuse(tmp_path):
    repo=tmp_path/'repo'; repo.mkdir()
    with pytest.raises(ValueError): s.external_output(repo/'output.json',repo)
    path=tmp_path/'existing.json'; path.write_bytes(b'x')
    with pytest.raises(ValueError): s.external_output(path,repo)


def test_final_synthetic_manifest_valid_and_deterministic(synthetic):
    first=p.build_publication(*synthetic); second=p.build_publication(*synthetic)
    assert s.canonical(first)==s.canonical(second)
    assert first['schema_version']=='l7_publication_manifest.v1'
    assert first['publication']['publication_state']=='READY_FOR_AUTHORIZED_PUBLICATION'
    assert len(first['artifacts'])==5
    assert 'self_digest' not in first and 'manifest_sha256' not in first


@pytest.mark.parametrize('mutation',[
 'missing','undeclared','malformed','zero','duplicate_role','duplicate_filename','asset_source','binding_source','validation_source',
 'changed_bytes','changed_size','missing_file','wrong_version','unknown_field','sbom_changed','checksum_changed'])
def test_final_builder_fail_closed(synthetic,mutation):
    sc,ab,vb,notes=synthetic
    if mutation=='missing': ab['artifacts'].pop()
    if mutation=='undeclared': ab['artifacts'][0]['role']='historical_mcpb'
    if mutation=='malformed': ab['artifacts'][0]['sha256']='TBD'
    if mutation=='zero': ab['artifacts'][0]['sha256']='0'*64
    if mutation=='duplicate_role': ab['artifacts'][1]['role']=ab['artifacts'][0]['role']
    if mutation=='duplicate_filename': ab['artifacts'][1]['filename']=ab['artifacts'][0]['filename']
    if mutation=='asset_source': ab['artifacts'][0]['source_tree']='a'*40
    if mutation=='binding_source': ab['source']=dict(ab['source'],commit='b'*40)
    if mutation=='validation_source': vb['validation']['native']['source_commit']='c'*40
    if mutation=='changed_bytes': Path(ab['artifacts'][0]['path']).write_bytes(b'CHANGED')
    if mutation=='changed_size': ab['artifacts'][0]['bytes']+=1
    if mutation=='missing_file': ab['artifacts'][0]['path']=str(notes.parent/'absent-file')
    if mutation=='wrong_version': ab['product_version']='1.0.0'
    if mutation=='unknown_field': ab['artifacts'][0]['unknown']='no'
    if mutation in {'sbom_changed','checksum_changed'}:
        role='first_party_sbom' if mutation=='sbom_changed' else 'native_checksum'
        row=next(r for r in ab['artifacts'] if r['role']==role); data=b'CHANGED\n'
        Path(row['path']).write_bytes(data); row.update(bytes=len(data),sha256=s.sha(data))
    with pytest.raises((ValueError,jsonschema.ValidationError)): p.build_publication(sc,ab,vb,notes)


def test_unaccepted_publication_state_rejected(synthetic):
    with pytest.raises(jsonschema.ValidationError): p.build_publication(*synthetic,publication_state='PENDING')


def test_policy_retains_mcpb_and_excludes_self_hash(contract):
    rows={r['role']:r for r in contract['artifact_set']}
    for role in ['native_zip','native_checksum','mcpb','mcpb_checksum','first_party_sbom','publication_manifest']:
        assert rows[role]['classification']=='PUBLICATION_ASSET'
    assert rows['docker']['classification']=='VALIDATION_ONLY'
    assert rows['github_source_zip']['classification']=='PLATFORM_GENERATED'
    assert rows['historical_mcpb']['classification']=='HISTORICAL_ONLY'
    assert rows['historical_v1_manifest']['classification']=='HISTORICAL_ONLY'
    schema=json.loads((s.ROOT/'docs/contracts/schemas/l7_publication_manifest.v1.schema.json').read_bytes())
    assert 'sha256' not in schema['properties'] and 'self_digest' not in schema['properties']


def test_sbom_external_regeneration_byte_equal(tmp_path):
    from scripts.dependency_authority import sbom,canonical
    raw=canonical(sbom()); external=tmp_path/'regenerated-sbom.json'; external.write_bytes(raw)
    assert raw==(s.ROOT/'config/first_party_dependency_sbom.json').read_bytes()
    assert len(json.loads(raw)['components'])==297


@pytest.mark.parametrize('data',[b'C:\\Users\\private-user\\x',b'D:\\private\\x',b'C:\\twmarket_temp\\x',
    b'github_pat_'+b'a'*40,b'-----BEGIN PRIVATE KEY-----\n'+b'A'*80+b'\n-----END PRIVATE KEY-----'])
def test_hygiene_private_paths_and_secrets_fail_closed(tmp_path,data):
    path=tmp_path/'payload.txt'; path.write_bytes(data)
    report=validate_artifact(path)
    assert report['status']=='FAIL'
    assert data.decode() not in json.dumps(report)


def test_hygiene_positive_and_zip_traversal(tmp_path):
    path=tmp_path/'benign.txt'; path.write_bytes(b'Ordinary public release content')
    assert validate_artifact(path)['status']=='PASS'
    archive=tmp_path/'unsafe.zip'
    with zipfile.ZipFile(archive,'w') as z: z.writestr('../escape.txt','x')
    assert validate_artifact(archive)['status']=='FAIL'


def test_release_notes_and_future_authorization_boundaries():
    notes=(s.ROOT/'docs/release/V1_5_0_RELEASE_NOTES_DRAFT.md').read_text(encoding='utf-8')
    for text in ['selected, unpublished','KNOWN_NOT_IMPLEMENTED','Python 3.12 is unsupported',
                 'STABLE_SOURCE_NOT_YET_FROZEN','FINAL_ARTIFACT_HASHES_NOT_YET_FROZEN','A7 and stable publication are NOT_AUTHORIZED']:
        assert text in notes
