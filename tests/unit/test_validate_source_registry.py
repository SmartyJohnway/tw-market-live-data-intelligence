from pathlib import Path
import copy, json
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
from scripts.validate_source_registry import validate_source_registry

def registry_args(reg=None):
    return (
        load('docs/source_registry/source_authority_registry.json') if reg is None else reg,
        load('docs/source_registry/source_risk_flag_catalog.json'),
        load('docs/source_registry/source_contract_schema.json'),
        load('docs/source_registry/source_family_coverage_matrix.json'),
    )

def test_validate_source_registry_ok():
    assert validate_source_registry(*registry_args()) == []

def test_source_registry_rejects_empty_or_missing_sources():
    assert any(e['code']=='registry_sources_empty' for e in validate_source_registry(*registry_args({'sources': []})))
    assert validate_source_registry(*registry_args({}))[0]['code'] == 'registry_sources_missing_or_not_array'

def test_source_registry_requires_six_core_sources():
    reg=load('docs/source_registry/source_authority_registry.json')
    reg['sources']=[s for s in reg['sources'] if s['source_id']!='TWSE_MIS']
    errors=validate_source_registry(*registry_args(reg))
    assert any(e['code']=='required_sources_missing' and 'TWSE_MIS' in e['source_ids'] for e in errors)

def test_source_registry_rejects_duplicate_source_id():
    reg=load('docs/source_registry/source_authority_registry.json')
    twse_mis=copy.deepcopy(next(s for s in reg['sources'] if s['source_id']=='TWSE_MIS'))
    reg['sources'].append(twse_mis)
    errors=validate_source_registry(*registry_args(reg))
    assert any(e['code']=='duplicate_source_id' and e['source_id']=='TWSE_MIS' for e in errors)

def test_source_registry_runs_schema_validator_for_array_boolean_and_contains():
    reg=load('docs/source_registry/source_authority_registry.json')
    bad=copy.deepcopy(reg['sources'][0])
    bad['allowed_roles']='not-array'
    bad['live_probe_authorization_required']='yes'
    bad['forbidden_roles']=[]
    bad['required_caveats']=[]
    reg['sources'][0]=bad
    codes={e['code'] for e in validate_source_registry(*registry_args(reg))}
    assert {'schema_type_mismatch','schema_contains_missing'} <= codes

def test_source_registry_malformed_entry_structured_no_traceback():
    reg=load('docs/source_registry/source_authority_registry.json')
    reg['sources'].append('not-object')
    errors=validate_source_registry(*registry_args(reg))
    assert any(e['code']=='source_entry_not_object' for e in errors)
