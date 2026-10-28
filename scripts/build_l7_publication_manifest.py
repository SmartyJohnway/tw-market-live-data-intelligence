"""Fail-closed deterministic final manifest from explicit source/artifact/evidence bindings."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.build_l7_rc_source_contract import canonical,sha,validate,external_output

BOUNDARY='REPRODUCIBLE_ROOTFS_CONTENT_WITH_EXPLICIT_OCI_METADATA_BOUNDARY'
LIMITATIONS=[
 ('NATIVE_TIER1','Windows 11 x64 is release-blocking Native Tier-1.'),
 ('PYTHON_RUNTIME','CPython 3.13 is canonical release/build/CI; 3.11 is noncanonical developer/source compatibility; 3.12 unsupported.'),
 ('MCP_EXACT_PIN','MCP remains exact mcp==1.29.0.'),
 ('WATCHLIST_MIGRATION','Watchlist v0 to v1 production migration is KNOWN_NOT_IMPLEMENTED.'),
 ('OCI_METADATA','Docker RootFS/content reproducibility has an explicit OCI metadata/timestamp nondeterminism boundary.'),
 ('SIGNING','Hashes, provenance and SBOM are not cryptographic publisher signatures; signing authority is NOT_ESTABLISHED.'),
 ('DIAGNOSTIC_PROFILES','Historical default-ci/full-non-network failures remain diagnostics, not canonical release blockers.'),
 ('HISTORICAL_M6G','Historical M6G live fallback is not current L7 release-live authority.'),
]


def input_schema(schema,key):
    return {'$schema':schema['$schema'],'$defs':schema['$defs'],'$ref':'#/$defs/'+key}


def build_publication(source_contract,artifact_binding,validation_binding,release_notes,publication_state='READY_FOR_AUTHORIZED_PUBLICATION'):
    schemas=ROOT/'docs/contracts/schemas'
    source_schema=json.loads((schemas/'l7_rc_source_contract.v1.schema.json').read_bytes())
    schema=json.loads((schemas/'l7_publication_manifest.v1.schema.json').read_bytes())
    validate(source_contract,source_schema)
    validate(artifact_binding,input_schema(schema,'artifact_binding'))
    validate(validation_binding,input_schema(schema,'validation_binding'))
    source=source_contract['source']; commit,tree=source['commit'],source['tree']
    for binding in (artifact_binding,validation_binding):
        if binding['source']!=source or binding['product_version']!=source_contract['product']['product_version']:
            raise ValueError('source/product binding mismatch')
    for evidence in validation_binding['validation'].values():
        if (evidence['source_commit'],evidence['source_tree'])!=(commit,tree):
            raise ValueError('validation source mismatch')
    policy={r['role']:r for r in source_contract['artifact_set'] if r['classification']=='PUBLICATION_ASSET' and r['role']!='publication_manifest'}
    rows=artifact_binding['artifacts']
    if len({r['role'] for r in rows})!=len(rows) or len({r['filename'].casefold() for r in rows})!=len(rows):
        raise ValueError('duplicate role/filename')
    if set(policy)!={r['role'] for r in rows}:
        raise ValueError('missing or undeclared publication asset')
    artifacts=[]; asset_bytes={}
    for row in rows:
        declared=policy[row['role']]
        if row['filename']!=declared['filename'] or row['media_type']!=declared['media_type']:
            raise ValueError('artifact-set filename/media disagreement')
        if (row['source_commit'],row['source_tree'])!=(commit,tree):
            raise ValueError('artifact source mismatch')
        p=Path(row['path'])
        if not p.is_absolute() or p.drive.upper()=='D:' or p.is_symlink() or not p.is_file():
            raise ValueError('explicit regular immutable asset required')
        if not p.resolve().is_relative_to(ROOT.parent):
            raise ValueError('asset input outside selected workspace')
        data=p.read_bytes()
        if len(data)!=row['bytes'] or sha(data)!=row['sha256']:
            raise ValueError('artifact bytes/hash mismatch')
        asset_bytes[row['role']]=data
        artifacts.append({k:v for k,v in row.items() if k!='path'})
    for role,checksum in [('native_zip','native_checksum'),('mcpb','mcpb_checksum')]:
        expected=(sha(asset_bytes[role])+'  '+policy[role]['filename']+'\n').encode()
        if asset_bytes[checksum]!=expected:
            raise ValueError('checksum sidecar identity mismatch')
    if sha(asset_bytes['first_party_sbom'])!=source_contract['dependency_authority']['first_party_sbom_sha256']:
        raise ValueError('SBOM export differs from accepted authority')
    if validation_binding['validation']['native']['native_zip_sha256']!=sha(asset_bytes['native_zip']):
        raise ValueError('Native validation refers to different artifact')
    notes=Path(release_notes).read_bytes()
    expected_notes=next((r['sha256'] for r in source_contract['governed_files'] if r['path']=='docs/release/V1_5_0_RELEASE_NOTES_DRAFT.md'),None)
    if sha(notes)!=expected_notes:
        raise ValueError('release notes differ from source authority')
    result={'schema_version':'l7_publication_manifest.v1','product':source_contract['product'],'source':source,
      'runtime_policy':source_contract['runtime_policy'],'dependency_authority':source_contract['dependency_authority'],
      'artifacts':sorted(artifacts,key=lambda row:row['role']),'validation':validation_binding['validation'],
      'provenance':{'dependency_authority_sha256':source_contract['dependency_authority']['dependency_authority_sha256'],
        'signing_policy':'SHA256_AND_RELEASE_PROVENANCE_PUBLISHER_SIGNATURE_NOT_ESTABLISHED',
        'publisher_surface':'GITHUB_RELEASE_WITH_SEPARATELY_AUTHORIZED_MCP_REGISTRY_UPDATE',
        'docker_reproducibility_boundary':BOUNDARY,'manifest_self_hash_policy':'MANIFEST_SELF_HASH_EXTERNAL_BINDING'},
      'release_notes':{'filename':'V1_5_0_RELEASE_NOTES_DRAFT.md','bytes':len(notes),'sha256':sha(notes)},
      'retained_limitations':[{'code':code,'description':description} for code,description in LIMITATIONS],
      'publication':{'tag':'v1.5.0','github_repository':source['repository'],'publication_state':publication_state}}
    validate(result,schema)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source-contract','artifact-binding','validation-binding','release-notes','output'):
        p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--publication-state',default='READY_FOR_AUTHORIZED_PUBLICATION')
    a=p.parse_args(); output=external_output(a.output)
    value=build_publication(json.loads(a.source_contract.read_bytes()),json.loads(a.artifact_binding.read_bytes()),
                            json.loads(a.validation_binding.read_bytes()),a.release_notes,a.publication_state)
    output.parent.mkdir(parents=True,exist_ok=True); output.write_bytes(canonical(value))
    print(json.dumps({'status':'PASS','output':str(output),'source':value['source']}))


if __name__=='__main__': main()
