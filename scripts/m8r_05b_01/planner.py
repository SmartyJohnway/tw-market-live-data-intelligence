"""Pure deterministic, non-authorizing M8R-05B-01 plan projection."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import jsonschema
from typing import Any, Mapping
from .artifact_loader import executor_index, verify_artifact
from .canonical import batch_group_id, canonical_json, canonical_operation_order, canonical_target_ids, canonical_warning_order, operation_id, plan_hash_and_id, sha256_json
from .models import PLAN_SCHEMA_VERSION, PLANNER_VERSION, PlanningError

_ROOT=Path(__file__).resolve().parents[2]
F3_SCHEMA=json.loads((_ROOT / 'schemas/unified_market_evidence_request_validation.v1.schema.json').read_text(encoding='utf-8'))
PLAN_SCHEMA=json.loads((_ROOT / 'schemas/unified_market_evidence_orchestration_plan.v1.schema.json').read_text(encoding='utf-8'))
F3_VALIDATOR=jsonschema.Draft7Validator(F3_SCHEMA)
PLAN_VALIDATOR=jsonschema.Draft7Validator(PLAN_SCHEMA, format_checker=jsonschema.FormatChecker())

F3_VERSION='unified_market_evidence_request_validation.v1'
ROUTING_VERSION='m8r_05b_capability_to_executor_routing_matrix.v1.draft'
HANDOFF_VERSION='m8r_05b_orchestration_handoff_contract.v1.draft'
CATALOG_VERSION='unified_market_evidence_capability_catalog.v1'

def _pairs(bindings: Mapping[str,Any]) -> list[tuple[str,str]]:
    refs=bindings.get('security_master_evidence_references'); hashes=bindings.get('security_master_artifact_hashes')
    if not isinstance(refs,list) or not isinstance(hashes,list) or not refs or len(refs)!=len(hashes): raise PlanningError('target_binding_invalid')
    if not all(isinstance(x,str) and x for x in refs+hashes) or len(set(refs))!=len(refs): raise PlanningError('target_binding_invalid')
    pairs=sorted(zip(refs,hashes))
    if len({h for _,h in pairs})!=len(pairs): raise PlanningError('target_binding_invalid','conflicting_duplicate_hash')
    return pairs

def _targets(validation: Mapping[str,Any]) -> list[dict[str,Any]]:
    result=[]
    for target in validation.get('target_results',[]):
        if target.get('resolution_status')!='resolved': continue
        identity=target.get('canonical_identity') or {}; tid=identity.get('canonical_target_id')
        if not isinstance(tid,str) or not tid: raise PlanningError('target_binding_invalid')
        result.append({'id':tid,'market':identity.get('market'),'security_type':identity.get('instrument_family') or identity.get('instrument_type')})
    return sorted(result,key=lambda x:x['id'])

def _validate_inputs(validation, catalog, routing, handoff, inventory, bindings):
    if validation.get('schema_version')!=F3_VERSION: raise PlanningError('input_schema_invalid')
    limits=validation.get('limits') or {}
    if (limits.get('operation_count_computed'),limits.get('operation_count'),limits.get('orchestrator_projection_required')) != (False,0,True): raise PlanningError('f3_invariant_mismatch')
    if list(F3_VALIDATOR.iter_errors(validation)): raise PlanningError('input_schema_invalid')
    if sha256_json(validation)!=bindings.get('f3_validation_output_hash'): raise PlanningError('f3_validation_hash_mismatch')
    verify_artifact(catalog,bindings.get('capability_catalog_hash'),code='capability_catalog_hash_mismatch',expected_version=CATALOG_VERSION)
    verify_artifact(routing,bindings.get('routing_matrix_hash'),code='routing_matrix_hash_mismatch',expected_version=ROUTING_VERSION)
    verify_artifact(handoff,bindings.get('handoff_contract_hash'),code='handoff_contract_hash_mismatch',expected_version=HANDOFF_VERSION)
    if bindings.get('planner_version')!=PLANNER_VERSION or bindings.get('routing_matrix_version')!=ROUTING_VERSION or bindings.get('handoff_contract_version')!=HANDOFF_VERSION: raise PlanningError('unsupported_contract_version')
    return _pairs(bindings),executor_index(inventory)

def _warning(cap, targets, reason): return {'code':'optional_capability_omitted','capability_id':cap,'canonical_target_ids':canonical_target_ids(targets),'severity':'warning','omission_reason':reason}


def _validate_batch_integrity(operations: list[dict[str, Any]], batch_groups: list[dict[str, Any]]) -> None:
    """Fail closed when executable batch membership is not a bijection."""
    ids=[group.get("batch_group_id") for group in batch_groups]
    if len(ids) != len(set(ids)): raise PlanningError("batch_contract_invalid", "duplicate_batch_group_id")
    operation_by_id={operation.get("operation_id"): operation for operation in operations}
    membership: dict[str, str] = {}
    for group in batch_groups:
        group_id=group["batch_group_id"]
        for operation_id_value in group.get("operation_ids", []):
            operation=operation_by_id.get(operation_id_value)
            if operation is None or operation_id_value in membership or operation.get("batch_group_id") != group_id:
                raise PlanningError("batch_contract_invalid", "batch_member_reference_invalid")
            membership[operation_id_value]=group_id
    for operation in operations:
        executable=operation.get("operation_status")=="executable_pending_approval"
        if executable != (operation.get("operation_id") in membership) or (not executable and operation.get("batch_group_id") is not None):
            raise PlanningError("batch_contract_invalid", "operation_batch_reference_invalid")

def plan_identity_scope(plan: Mapping[str, Any]) -> dict[str, Any]:
    scope={k:plan[k] for k in ('schema_version','input_bindings','plan_status','operations','batch_groups','accounting','blocked_operations','omitted_optional_capabilities','package_approval_requirements')}
    bindings=plan['input_bindings']
    scope.update({'canonical_operation_ordering':'f3_capability_market_executor_target_parameters_batch_operation_id','planner_version':PLANNER_VERSION,'routing_matrix_version':bindings['routing_matrix_version'],'routing_matrix_hash':bindings['routing_matrix_hash'],'handoff_contract_version':bindings['handoff_contract_version'],'handoff_contract_hash':bindings['handoff_contract_hash']})
    return scope

def build_plan(validation: Mapping[str,Any], *, capability_catalog: Mapping[str,Any], routing_matrix: Mapping[str,Any], handoff_contract: Mapping[str,Any], executor_disposition: Mapping[str,Any], input_bindings: Mapping[str,Any], planning_timestamp: str) -> dict[str,Any]:
    """Return a deep-independent plan; all inputs and timestamp are explicit."""
    validation,catalog,routing,handoff,inventory,bindings=map(copy.deepcopy,(validation,capability_catalog,routing_matrix,handoff_contract,executor_disposition,input_bindings))
    pairs, executors=_validate_inputs(validation,catalog,routing,handoff,inventory,bindings)
    if not isinstance(planning_timestamp,str) or not planning_timestamp.endswith('Z'): raise PlanningError('input_schema_invalid','planning_timestamp')
    status=validation.get('validation_status')
    targets=_targets(validation); catalog_caps={x.get('capability_id'):x for x in catalog.get('data_need_capabilities',[]) if isinstance(x,dict)}; routes={x.get('capability_id'):x for x in routing.get('routes',[]) if isinstance(x,dict)}
    ops=[]; blocked=[]; omissions=[]; warnings=[]
    if status in {'requires_clarification','unsupported'}:
        plan_status=status
    elif status!='valid' or validation.get('request_schema_status')!='valid' or any(t.get('resolution_status')!='resolved' for t in validation.get('target_results',[])):
        plan_status='blocked'
    else:
        plan_status='plan_ready'
        for cap in sorted(validation.get('capability_results',[]),key=lambda x:x.get('data_need_index',0)):
            cid=cap.get('capability_id'); priority=cap.get('priority'); route=routes.get(cid); params=(validation.get('normalized_request',{}).get('data_needs',[{}]* (cap.get('data_need_index',0)+1))[cap.get('data_need_index',0)].get('parameters',{}))
            target_ids=[t['id'] for t in targets] if route and route.get('target_required') else []
            cap_status=cap.get('status')
            reason=(cap.get('reason_codes') or ['route_unavailable'])[0]
            if not route or cap_status in {'unsupported','unknown','invalid_parameters','requires_target_resolution'} or route.get('routing_status')=='blocked':
                if priority=='optional':
                    omissions.append({'capability_id':cid,'canonical_target_ids':canonical_target_ids(target_ids),'reason_code':reason,'severity':'warning','normalized_parameters':params}); warnings.append(_warning(cid,target_ids,reason)); continue
                blocked.append({'capability_id':cid,'canonical_target_ids':canonical_target_ids(target_ids),'market':None,'parameters':params,'executor_id':None,'batch_group_id':None,'network_required':False,'expected_evidence_contract':(route or {}).get('output_evidence_contract','unavailable capability'),'blocking_reason_codes':[reason],'executor_invocation_eligible':False}); plan_status='blocked'; continue
            route_status=route.get('routing_status')
            executable=route_status=='resolved' and cap_status=='runtime_executable' and not route.get('provisional')
            if executable:
                eid=route.get('selected_executor_id'); ex=executors.get(eid)
                if not ex or ex.get('reusable_for_05b') is not True or ex.get('disposition')!='adapter_required': raise PlanningError('selected_executor_invalid')
            elif cap_status=='provisional' or route_status=='plan_only' or cap_status=='contract_supported':
                if priority=='required': plan_status='plan_only_not_executable' if plan_status!='blocked' else plan_status
            else: raise PlanningError('executor_route_missing')
            units=targets if route.get('target_required') else [{'id':None,'market':None,'security_type':None}]
            for unit in units:
                market=unit['market']; tids=[unit['id']] if unit['id'] else []
                catalog_cap=catalog_caps.get(cid, {})
                provisional_market=market in catalog_cap.get('provisional_markets', [])
                mismatch=(market is not None and not provisional_market and market not in route.get('supported_markets', [])) or (bool(route.get('supported_security_types')) and unit['security_type'] not in route.get('supported_security_types', []))
                if mismatch:
                    mismatch_reason='unsupported_market' if market not in route.get('supported_markets', []) else 'unsupported_security_type'
                    if priority=='optional':
                        omissions.append({'capability_id':cid,'canonical_target_ids':canonical_target_ids(tids),'reason_code':mismatch_reason,'severity':'warning','normalized_parameters':params}); warnings.append(_warning(cid,tids,mismatch_reason)); continue
                    blocked.append({'capability_id':cid,'canonical_target_ids':canonical_target_ids(tids),'market':market,'parameters':params,'executor_id':None,'batch_group_id':None,'network_required':False,'expected_evidence_contract':route['output_evidence_contract'],'blocking_reason_codes':[mismatch_reason],'executor_invocation_eligible':False}); plan_status='blocked'; continue
                if cap_status=='provisional' or provisional_market:
                    executable=False
                    if priority=='required' and plan_status!='blocked': plan_status='plan_only_not_executable'
                batch_scope={'executor_id':route.get('selected_executor_id') if executable else None,'capability_id':cid,'market':market,'parameters':params,'expected_evidence_contract':route['output_evidence_contract'],'network_required':bool(executable and route.get('network_required')),'approval_required':bool(route.get('capability_requires_execution_approval'))}
                bkey=sha256_json(batch_scope)
                scope={'capability_id':cid,'canonical_target_ids':canonical_target_ids(tids),'market':market,'security_types':[unit['security_type']] if unit['security_type'] else [],'normalized_parameters':params,'executor_id':route.get('selected_executor_id') if executable else None,'batch_key':bkey,'expected_evidence_contract':route['output_evidence_contract'],'operation_status':'executable_pending_approval' if executable else 'plan_only_not_executable','network_required':bool(executable and route.get('network_required')),'capability_requires_execution_approval':bool(route.get('capability_requires_execution_approval')),'dependency_operation_ids':[]}
                op={'operation_id':operation_id(scope),'capability_id':cid,'canonical_target_ids':scope['canonical_target_ids'],'market':market,'security_types':scope['security_types'],'parameters':params,'executor_id':scope['executor_id'],'batch_group_id':None,'operation_status':scope['operation_status'],'network_required':scope['network_required'],'capability_requires_execution_approval':scope['capability_requires_execution_approval'],'expected_evidence_contract':scope['expected_evidence_contract'],'blocking_reason_codes':[],'warnings':[],'executor_invocation_eligible':executable,'dependency_operation_ids':[],'_batch_key':bkey,'_batching_scope':route.get('batching_scope'),'_source_compatibility_key':route.get('source_compatibility_key') or route.get('selected_executor_id')}
                ops.append(op)
    # Derived capabilities never invoke a source and bind by deterministic operation ID.
    primary_ids=sorted(op['operation_id'] for op in ops if op['operation_status']=='executable_pending_approval')
    for op in ops:
        if op['capability_id'] in {'source_currentness','evidence_quality'}:
            op['dependency_operation_ids']=primary_ids
            if not primary_ids: op['warnings']=[{'code':'upstream_evidence_operation_missing','capability_id':op['capability_id'],'canonical_target_ids':op['canonical_target_ids'],'severity':'warning','omission_reason':'upstream_evidence_operation_missing'}]
            identity={'capability_id':op['capability_id'],'canonical_target_ids':op['canonical_target_ids'],'market':op['market'],'security_types':op['security_types'],'normalized_parameters':op['parameters'],'executor_id':op['executor_id'],'batch_key':op['_batch_key'],'expected_evidence_contract':op['expected_evidence_contract'],'operation_status':op['operation_status'],'network_required':op['network_required'],'capability_requires_execution_approval':op['capability_requires_execution_approval'],'dependency_operation_ids':op['dependency_operation_ids']}
            op['operation_id']=operation_id(identity)
    # Group only executable operations according to the declared routing batching scope.
    groups={}
    for op in ops:
        if op['operation_status']!='executable_pending_approval': continue
        batching_scope=op['_batching_scope']
        if batching_scope not in {'none','same_market','same_source'}: raise PlanningError('batch_contract_invalid')
        base=(op['_batch_key'],op['executor_id'],op['capability_id'],op['market'])
        if batching_scope=='none': key=base+(op['operation_id'],)
        elif batching_scope=='same_market': key=base
        else:
            source_key=op['_source_compatibility_key']
            if not isinstance(source_key,str) or not source_key: raise PlanningError('batch_contract_invalid')
            key=base+(source_key,)
        groups.setdefault(key,[]).append(op)
    batch_groups=[]
    for key,members in sorted(groups.items()):
        first=members[0]; scope=first['_batching_scope']; operation_ids=sorted(x['operation_id'] for x in members)
        identity={'batching_scope':scope,'executor_id':first['executor_id'],'capability_id':first['capability_id'],'market':first['market'],'normalized_parameters':first['parameters'],'expected_evidence_contract':first['expected_evidence_contract'],'network_required':first['network_required'],'capability_requires_execution_approval':first['capability_requires_execution_approval'],'operation_ids':operation_ids}
        if scope=='same_source': identity['source_compatibility_key']=first['_source_compatibility_key']
        bid=batch_group_id(identity)
        for op in members: op['batch_group_id']=bid
        batch_groups.append({'batch_group_id':bid,'executor_id':first['executor_id'],'capability_id':first['capability_id'],'market':first['market'],'operation_ids':operation_ids,'network_required':True,'capability_requires_execution_approval':first['capability_requires_execution_approval']})
    order={x.get('capability_id'):i for i,x in enumerate(sorted(validation.get('capability_results',[]),key=lambda x:x.get('data_need_index',0)))}
    batch_keys={op['operation_id']:op['_batch_key'] for op in ops}; ops=[{k:v for k,v in op.items() if k not in {'_batch_key','_batching_scope','_source_compatibility_key'}} for op in canonical_operation_order(ops,capability_order_by_id=order,batch_key_by_operation_id=batch_keys)] if ops else []
    _validate_batch_integrity(ops, batch_groups)
    operation_ids={op['operation_id'] for op in ops}
    for op in ops:
        dependencies=op['dependency_operation_ids']
        if dependencies != sorted(set(dependencies)) or op['operation_id'] in dependencies or not set(dependencies).issubset(operation_ids):
            raise PlanningError('target_binding_invalid','dependency_operation_ids_invalid')
    warnings=canonical_warning_order(warnings); omissions=sorted(omissions,key=canonical_json); blocked=sorted(blocked,key=canonical_json); batch_groups=sorted(batch_groups,key=lambda x:x['batch_group_id'])
    executable=[o for o in ops if o['operation_status']=='executable_pending_approval']
    logical=len(ops)+len(blocked); hard=catalog.get('bounds',{}).get('hard_operation_limit')
    if not isinstance(hard,int) or logical>hard: raise PlanningError('operation_limit_exceeded')
    if plan_status=='plan_ready' and warnings: plan_status='plan_ready_with_warnings'
    accounting={'logical_operation_count':logical,'batch_group_count':len(batch_groups),'executor_invocation_count':len(batch_groups),'network_request_estimate':len(batch_groups),'planned_evidence_bundle_count':1 if executable else 0}
    approval={'package_requires_owner_approval':any(o['capability_requires_execution_approval'] for o in executable),'authorization_eligible':bool(executable) and plan_status in {'plan_ready','plan_ready_with_warnings'},'approval_policy':'strictest_operation_controls_package','approval_reason_codes':['execution_approval_required'] if any(o['capability_requires_execution_approval'] for o in executable) else []}
    bindings['security_master_evidence_references']=[r for r,_ in pairs]; bindings['security_master_artifact_hashes']=[h for _,h in pairs]
    plan={'schema_version':PLAN_SCHEMA_VERSION,'execution_authorized':False,'input_bindings':bindings,'planner_metadata':{'planning_timestamp':planning_timestamp,'offline':True,'deterministic':True,'limit_source':'catalog.hard_operation_limit'},'plan_status':plan_status,'operations':ops,'batch_groups':batch_groups,'accounting':accounting,'warnings':warnings,'blocked_operations':blocked,'omitted_optional_capabilities':omissions,'evidence_references':bindings['security_master_evidence_references'],'package_approval_requirements':approval}
    scope=plan_identity_scope(plan)
    plan['plan_hash'],plan['plan_id']=plan_hash_and_id(scope)
    if list(PLAN_VALIDATOR.iter_errors(plan)): raise PlanningError('output_schema_invalid')
    return copy.deepcopy(plan)
