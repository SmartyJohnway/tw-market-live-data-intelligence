import ast
import json
from pathlib import Path
from scripts.m8r_03e_context_validator import canonical_json, validate_schema, validate_watchlist_ai_context_package, validate_watchlist_conversation_handoff
from scripts.m8r_03e_v1_to_v2_migration import migrate_watchlist_ai_context_package_v1_to_v2
from scripts.m8r_03e_watchlist_ai_context_builder import build_watchlist_ai_context_package
from scripts.m8r_03e_conversation_handoff_builder import compose_conversation_handoff
ROOT=Path(__file__).resolve().parents[2]
FIX=ROOT/'tests/fixtures/m8r_03e_r3/historical_v1_context_package.json'
COMPLETE=ROOT/'tests/fixtures/m8r_03e/complete_snapshot'

def test_historical_v1_migration_preserves_evidence_and_is_canonical():
    legacy=json.loads(FIX.read_text(encoding="utf-8"))
    assert validate_schema(legacy,'m8r_watchlist_ai_context_package.v1.schema.json') is None
    a=migrate_watchlist_ai_context_package_v1_to_v2(legacy); b=migrate_watchlist_ai_context_package_v1_to_v2(legacy)
    assert validate_schema(a,'m8r_watchlist_ai_context_package.v2.schema.json') is None
    assert canonical_json(a)==canonical_json(b) and a['package_hash']==b['package_hash']
    for key in ('request','citation_index','missing_evidence','caveats'):
        assert a[key]==legacy[key]
    assert a['source_lineage']['bundle_id']==legacy['source_lineage']['bundle_id']
    assert a['context_budget']['policy']==legacy['context_budget']['policy']
    assert a['targets'][0]['current_observation']==legacy['targets'][0]['current_observation']
    assert a['targets'][0]['eod_reference']==legacy['targets'][0]['eod_reference']
    assert a['targets'][0]['performance']==legacy['targets'][0]['performance']
    assert 'conversation_scope' not in a and 'prohibitions' not in a
    assert all('allowed_interpretations' not in t and 'prohibited_inferences' not in t for t in a['targets'])
    assert any('stale_evidence_not_current' in x['reason'] for x in a['evidence_limitations'])
    assert any('adjusted return' in x['reason'] for x in a['evidence_limitations'])
    assert a['source_lineage']['migration']['legacy_counts']['citation_count']==len(legacy['citation_index'])
    assert a['source_lineage']['migration']['v2_counts_verified'] is True

def _evidence():
    req,plan,res,bundle=[json.loads((COMPLETE/n).read_text(encoding="utf-8")) for n in ('request.json','execution_plan.json','execution_result.json','bundle.json')]
    return build_watchlist_ai_context_package(validated_request=req,execution_plan=plan,execution_result=res,watchlist_bundle=bundle,generated_at_utc='2026-07-16T03:00:00Z')

def test_agent_policy_composition_does_not_mutate_evidence():
    evidence=_evidence(); before=canonical_json(evidence)
    policy_a={'conversation_policy':{'recommendations_permitted':False,'trading_advice_permitted':False}}
    policy_b={'conversation_policy':{'recommendations_permitted':True,'trading_advice_permitted':True}}
    a=compose_conversation_handoff(evidence_package=evidence,agent_policy=policy_a,generated_at_utc='2026-07-16T03:00:00Z')
    b=compose_conversation_handoff(evidence_package=evidence,agent_policy=policy_b,generated_at_utc='2026-07-16T03:00:00Z')
    assert canonical_json(evidence)==before
    assert a['context_package_id']==b['context_package_id']==evidence['context_package_id']
    assert a['response_constraints'] != b['response_constraints']
    assert validate_watchlist_conversation_handoff(a,context_package=evidence)['valid']
    assert validate_watchlist_conversation_handoff(b,context_package=evidence)['valid']

def test_critical_evidence_modules_have_no_product_policy_imports():
    forbidden={'config.agent_policy','scripts.m8r_03e_conversation_handoff_builder','product_response_policy','conversation_policy'}
    for rel in ('scripts/m8r_03e_watchlist_ai_context_builder.py','scripts/m8r_03e_context_validator.py','scripts/m8r_03d_watchlist_controlled_executor.py'):
        tree=ast.parse((ROOT/rel).read_text(encoding="utf-8"))
        modules={node.module for node in ast.walk(tree) if isinstance(node,ast.ImportFrom) and node.module} | {alias.name for node in ast.walk(tree) if isinstance(node,ast.Import) for alias in node.names}
        assert not any(module == blocked or module.startswith(blocked+'.') for module in modules for blocked in forbidden), (rel,modules)
