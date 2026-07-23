import json
from pathlib import Path
import jsonschema
from tests.unit.test_m8r_05b_01_planner import validation,plan
SCHEMA=json.load(open('schemas/unified_market_evidence_orchestration_plan.v1.schema.json'))
def test_golden_artifacts_are_schema_valid_and_non_authorizing():
 for path in Path('tests/fixtures/m8r_05b_01/golden').glob('*.json'):
  value=json.load(open(path));jsonschema.Draft7Validator(SCHEMA,format_checker=jsonschema.FormatChecker()).validate(value);assert value['execution_authorized'] is False
def test_timestamp_does_not_change_identity():
 a=plan(validation(),timestamp='2026-07-23T00:00:00Z');b=plan(validation(),timestamp='2026-07-24T00:00:00Z');assert (a['plan_hash'],a['plan_id'],[x['operation_id'] for x in a['operations']])==(b['plan_hash'],b['plan_id'],[x['operation_id'] for x in b['operations']])
