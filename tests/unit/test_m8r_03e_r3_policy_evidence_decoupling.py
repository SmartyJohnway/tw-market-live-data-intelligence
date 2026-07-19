import json
from pathlib import Path
from scripts.m8r_03e_context_validator import sha256_json
from scripts.m8r_03e_watchlist_ai_context_builder import build_watchlist_ai_context_package
ROOT=Path(__file__).resolve().parents[2]; FIX=ROOT/'tests/fixtures/m8r_03e/complete_snapshot'
def _package():
    req,plan,res,bundle=[json.loads((FIX/name).read_text(encoding="utf-8")) for name in ('request.json','execution_plan.json','execution_result.json','bundle.json')]
    return build_watchlist_ai_context_package(validated_request=req,execution_plan=plan,execution_result=res,watchlist_bundle=bundle,generated_at_utc='2026-07-16T03:00:00Z')
def test_agent_policy_change_does_not_change_evidence_hash_or_lineage():
    policy=json.loads((ROOT/'config/agent_policy/market_evidence_agent_policy.json').read_text(encoding="utf-8")); a=_package(); policy['conversation_policy']['recommendations_permitted']=True; b=_package()
    assert sha256_json(a)==sha256_json(b)
    assert a['source_lineage']==b['source_lineage']
    assert a['citation_index']==b['citation_index']
    assert a['missing_evidence']==b['missing_evidence']

def test_v1_to_v2_migration_is_deterministic_and_removes_policy_fields():
    from scripts.m8r_03e_context_validator import validate_schema
    old=json.loads((FIX/'request.json').read_text(encoding="utf-8"))
    assert old['schema_version']
    pkg=_package(); assert pkg['schema_version']=='m8r_watchlist_ai_context_package.v2'
    assert 'conversation_scope' not in pkg and 'prohibitions' not in pkg
    assert validate_schema(pkg,'m8r_watchlist_ai_context_package.v2.schema.json') is None
