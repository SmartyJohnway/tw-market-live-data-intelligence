from __future__ import annotations
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONVERSATION_CONTRACT_PATH = ROOT/'docs/data_capabilities/m8r_03b_conversation_scope_contract.json'
EVIDENCE_BUNDLE_CONTRACT_PATH = ROOT/'docs/data_capabilities/m8r_03b_evidence_bundle_contracts.json'
SUPPORTED_CONVERSATION_CONTRACT = 'm8r_03b_conversation_scope_contract.v2'
SUPPORTED_EVIDENCE_CONTRACT = 'm8r_03b_evidence_bundle_contracts.v2'
SUPPORTED_RUNTIME_SCHEMAS = {
    'm8r_ai_market_conversation_intent.v1','m8r_ai_evidence_request.v1',
    'm8r_watchlist_snapshot_request.v1','m8r_watchlist_snapshot_bundle.v1',
    'm8r_watchlist_performance_request.v1','m8r_watchlist_performance_bundle.v1',
    'm8r_watchlist_input_observation.v1',
}
KNOWN_TYPES = {'string','integer','number','boolean','object','array'}

class M8R03CContractError(ValueError):
    def __init__(self, code: str, path: str, detail: str):
        self.code=code; self.path=path; self.detail=detail
        super().__init__(f'{code}:{path}:{detail}')

def _load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise M8R03CContractError('contract_file_missing', str(path), 'contract file missing')
    try:
        data=json.loads(path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        raise M8R03CContractError('invalid_json', str(path), 'invalid JSON') from None
    if not isinstance(data, dict):
        raise M8R03CContractError('contract_root_invalid', str(path), 'root must be object')
    return data

def _field_name(field: dict[str, Any], path: str) -> str:
    name=field.get('field_name')
    if not isinstance(name, str) or not name:
        raise M8R03CContractError('required_contract_section_missing', path, 'field_name missing')
    return name

def _validate_fields(fields: Any, path: str) -> None:
    if not isinstance(fields, list):
        raise M8R03CContractError('required_contract_section_missing', path, 'fields/properties must be list')
    seen=set()
    for i, field in enumerate(fields):
        if not isinstance(field, dict):
            raise M8R03CContractError('required_contract_section_missing', f'{path}[{i}]', 'field must be object')
        name=_field_name(field, f'{path}[{i}]')
        if name in seen:
            raise M8R03CContractError('duplicate_field_definition', f'{path}.{name}', 'duplicate field')
        seen.add(name)
        typ=field.get('type')
        if typ not in KNOWN_TYPES:
            raise M8R03CContractError('unknown_type_declaration', f'{path}.{name}', str(typ))
        enum=field.get('enum')
        if enum is not None and (not isinstance(enum, list) or not enum or len(set(map(str, enum))) != len(enum)):
            raise M8R03CContractError('invalid_enum_declaration', f'{path}.{name}', 'enum must be non-empty unique list')
        if typ == 'object' and 'properties' in field:
            _validate_fields(field['properties'], f'{path}.{name}.properties')

def load_conversation_contract(path: Path | str = CONVERSATION_CONTRACT_PATH) -> dict[str, Any]:
    data=_load(Path(path))
    if data.get('schema_version') != SUPPORTED_CONVERSATION_CONTRACT:
        raise M8R03CContractError('unsupported_contract_schema_version', str(path), str(data.get('schema_version')))
    if not isinstance(data.get('conversation_intent'), dict):
        raise M8R03CContractError('required_contract_section_missing', 'conversation_intent', 'missing')
    _validate_fields(data['conversation_intent'].get('fields'), 'conversation_intent.fields')
    for key in ('scope_modes','time_modes','evidence_depth_modes'):
        if not isinstance(data.get(key), dict) or not isinstance(data[key].get('enum'), list):
            raise M8R03CContractError('required_contract_section_missing', key, 'missing enum')
    return deepcopy(data)

def load_evidence_bundle_contract(path: Path | str = EVIDENCE_BUNDLE_CONTRACT_PATH) -> dict[str, Any]:
    data=_load(Path(path))
    if data.get('schema_version') != SUPPORTED_EVIDENCE_CONTRACT:
        raise M8R03CContractError('unsupported_contract_schema_version', str(path), str(data.get('schema_version')))
    for key in ('common_evidence_request','record_types','common_bundle_envelope','bundles'):
        if key not in data:
            raise M8R03CContractError('required_contract_section_missing', key, 'missing')
    _validate_fields(data['common_evidence_request'].get('fields'), 'common_evidence_request.fields')
    _validate_fields(data['common_bundle_envelope'].get('fields'), 'common_bundle_envelope.fields')
    return deepcopy(data)

def compile_contract_metadata() -> dict[str, Any]:
    c=load_conversation_contract(); e=load_evidence_bundle_contract()
    statuses=set()
    coverage=set()
    for rec in e.get('record_types', {}).values():
        for f in rec.get('fields', []) if isinstance(rec,dict) else []:
            if f.get('field_name') == 'calculation_status': statuses.update(f.get('enum', []))
            if f.get('field_name') == 'coverage_state': coverage.update(f.get('enum', []))
    return {'scope_modes': tuple(c['scope_modes']['enum']), 'time_modes': tuple(c['time_modes']['enum']), 'evidence_depth_modes': tuple(c['evidence_depth_modes']['enum']), 'calculation_statuses': tuple(sorted(statuses)) or ('calculated','partial','input_unavailable','formula_not_applicable','stale_inputs','error'), 'coverage_states': tuple(sorted(coverage)) or ('partial','unavailable','usable')}

def get_scope_modes(): return compile_contract_metadata()['scope_modes']
def get_time_modes(): return compile_contract_metadata()['time_modes']
def get_evidence_depth_modes(): return compile_contract_metadata()['evidence_depth_modes']
def get_calculation_statuses(): return compile_contract_metadata()['calculation_statuses']
def get_coverage_states(): return compile_contract_metadata()['coverage_states']
