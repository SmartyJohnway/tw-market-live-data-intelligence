"""External deterministic source contract for a clean immutable Git HEAD."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import jsonschema

ROOT=Path(__file__).resolve().parents[1]
SCHEMA='docs/contracts/schemas/l7_rc_source_contract.v1.schema.json'
DEPENDENCIES={
    'requirements_lock_sha256':'requirements-lock.txt',
    'dependency_authority_sha256':'config/dependency_authority.json',
    'native_wheelhouse_lock_sha256':'packaging_native/wheelhouse-lock.json',
    'docker_wheelhouse_lock_sha256':'packaging_docker/dependency-lock-linux-amd64-cp313.json',
    'first_party_sbom_sha256':'config/first_party_dependency_sbom.json',
}
GOVERNED=[SCHEMA,'docs/contracts/schemas/l7_publication_manifest.v1.schema.json',
          'docs/contracts/L7_RELEASE_SOURCE_AND_PUBLICATION_MANIFEST_CONTRACT.md',
          'config/l7_release_artifact_set.v1.json','scripts/build_l7_rc_source_contract.py',
          'scripts/build_l7_publication_manifest.py','scripts/validate_l7_release_artifact_hygiene.py',
          'scripts/build_mcpb_distribution.py','scripts/accept_mcpb_distribution.py',
          'packaging_mcpb/manifest.template.json','packaging_mcpb/resource-policy.json',
          'packaging_mcpb/record.py','packaging_mcpb/hygiene.py',
          'packaging_mcpb/upstream/mcpb-manifest-v0.3.schema.json','packaging_mcpb/upstream/provenance.json',
          'packaging_mcpb/upstream/LICENSE','packaging_mcpb/README-PACKAGE.md',
          'packaging_native/resource-policy.json','docs/release/V1_5_0_RELEASE_NOTES_DRAFT.md',
          'VERSION',*DEPENDENCIES.values()]
RUNTIME={'canonical_python':'CPython 3.13','native_os':'Windows 11','native_arch':'x64',
         'docker_platform':'linux/amd64','mcp_sdk_policy':'mcp==1.29.0'}


def canonical(value):
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()


def sha(data): return hashlib.sha256(data).hexdigest()


def git(root,*args):
    return subprocess.check_output(['git','-c','core.hooksPath=NUL',*args],cwd=root)


def validate(value,schema):
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator(schema,format_checker=jsonschema.FormatChecker()).validate(value)


def external_output(output,root=ROOT):
    output=Path(output)
    if not output.is_absolute() or output.drive.upper()=='D:':
        raise ValueError('explicit external C: output required')
    output=output.resolve(); root=Path(root).resolve()
    if output.is_relative_to(root) or not output.is_relative_to(root.parent) or output.exists():
        raise ValueError('fresh external workspace output required')
    return output


def build_source_contract(root=ROOT):
    root=Path(root).resolve()
    if git(root,'status','--porcelain','--untracked-files=all').strip():
        raise ValueError('source must be clean and committed')
    blob=lambda p:git(root,'show','HEAD:'+p)
    if blob('VERSION').decode('utf-8').strip()!='1.5.0':
        raise ValueError('VERSION must be 1.5.0')
    policy=json.loads(blob('config/l7_release_artifact_set.v1.json'))
    if set(policy)!={'schema_version','product_version','registry_publication','manifest_self_hash_policy','artifacts'} or policy['schema_version']!='l7_release_artifact_set.v1' or policy['product_version']!='1.5.0' or policy['registry_publication'] is not False or policy['manifest_self_hash_policy']!='MANIFEST_SELF_HASH_EXTERNAL_BINDING':
        raise ValueError('artifact-set policy identity mismatch')
    rows=policy['artifacts']
    if len({r['role'] for r in rows})!=len(rows) or len({r['filename'] for r in rows})!=len(rows):
        raise ValueError('duplicate artifact policy')
    result={'schema_version':'l7_rc_source_contract.v1',
      'product':{'name':'TW-Market Live Data Intelligence','product_version':'1.5.0'},
      'source':{'commit':git(root,'rev-parse','HEAD').decode().strip(),'tree':git(root,'rev-parse','HEAD^{tree}').decode().strip(),
                'repository':'SmartyJohnway/tw-market-live-data-intelligence','source_contract_version':'l7_rc_source_contract.v1'},
      'runtime_policy':RUNTIME,'dependency_authority':{k:sha(blob(p)) for k,p in DEPENDENCIES.items()},
      'artifact_set_policy_sha256':sha(blob('config/l7_release_artifact_set.v1.json')),'artifact_set':rows,
      'governed_files':[{'path':p,'sha256':sha(blob(p))} for p in sorted(set(GOVERNED))],
      'expected_validations':['canonical_ci','native','docker','compatibility','bounded_live','artifact_hygiene'],
      'stable_source_frozen':False,'final_artifacts_frozen':False,
      'self_reference_policy':'EXTERNAL_INSTANCE_FROM_IMMUTABLE_SOURCE_AND_MANIFEST_SELF_HASH_EXTERNAL_BINDING'}
    validate(result,json.loads(blob(SCHEMA)))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); output=external_output(a.output)
    value=build_source_contract(); output.parent.mkdir(parents=True,exist_ok=True); output.write_bytes(canonical(value))
    print(json.dumps({'status':'SOURCE_CONTRACT_DRY_RUN_ONLY','source':value['source'],'output':str(output)}))


if __name__=='__main__': main()
