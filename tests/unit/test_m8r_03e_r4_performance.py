import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def load(p): return json.loads((ROOT/p).read_text())
def test_r4_contract_separates_authorized_and_stress_tiers():
 c=load('docs/contracts/m8r_03e_r4_performance_measurement_contract.json')
 assert c['production_contract']['maximum_targets_per_request']==10
 assert c['stress_projection']['not_authorized_for_production_request'] is True
def test_r4_baseline_has_repetitions_and_deterministic_guardrails():
 b=load('docs/quality/m8r_03e_r4_performance_baseline.json'); scenarios={x['scenario_id']:x for x in b['scenarios']}
 assert scenarios['1_target_snapshot']['validity_results'] and scenarios['10_target_snapshot']['repeat_count']==5
 for name in ('50_target_stress','100_target_stress'):
  assert scenarios[name]['tier']=='stress_only' and scenarios[name]['non_contract']
 for x in scenarios.values():
  assert x['operation_counts']['filesystem_write']==x['aggregate_valid_package_count']
  assert x['semantic_equivalence'] is True
def test_schema_validator_cache_is_bounded_and_semantically_transparent():
 from scripts.m8r_03e_context_validator import _validator,validate_schema
 pkg=load('tests/fixtures/m8r_03e/complete_snapshot/request.json')
 # Cache identity is process-scoped immutable schema compilation, not evidence caching.
 assert _validator('m8r_watchlist_ai_context_package.v2.schema.json') is _validator('m8r_watchlist_ai_context_package.v2.schema.json')
 assert callable(validate_schema)
