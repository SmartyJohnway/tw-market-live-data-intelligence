#!/usr/bin/env python3
"""Network-free integrity validator for the frozen J4 regression candidate."""
from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts import phase_j_j4_regression_authority as j4


SCHEMA_HASHES = {'docs/governance/phase_j/PHASE_J_J4_REGRESSION_CHANGE_MANIFEST_SCHEMA_V1.json': 'ff0b5d8e0cf22673e234a9241532757f9b37ca5c0bc7d85aeb76c3e4e1e7d7fc', 'docs/governance/phase_j/PHASE_J_J4_REGRESSION_RECEIPT_SCHEMA_V1.json': 'c8ac4949aba86a1323ff2305d9835584f664b11b1aa5f911eef1101911dd2ac8'}

def validate(check_git=True):
    a = j4.validate_authority()
    from jsonschema import Draft202012Validator
    for path, expected in SCHEMA_HASHES.items():
        schema = j4.load(ROOT / path)
        Draft202012Validator.check_schema(schema)
        j4.require(j4.file_hash(ROOT / path) == expected, 'ACCEPTANCE_SCHEMA_DRIFT')
    if check_git:
        def git(*args):
            return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()
        j4.require(git('rev-parse', a['starting_authority']['head'] + '^{tree}') == a['starting_authority']['tree'], 'PHASE_J_J4_BASELINE_DRIFT')
        j4.require(git('rev-parse', 'origin/main') == a['starting_authority']['main'], 'PHASE_J_J4_BASELINE_DRIFT')
        j4.require(git('branch', '--show-current') == a['starting_authority']['branch'], 'PHASE_J_J4_BASELINE_DRIFT')
        subprocess.run(['git', 'merge-base', '--is-ancestor', a['starting_authority']['head'], 'HEAD'], cwd=ROOT, check=True)
        changed = git('diff', '--name-only', a['starting_authority']['head'], 'HEAD').splitlines()
        allowed = ('docs/governance/phase_j/PHASE_J_J4_', 'scripts/phase_j_j4_', 'scripts/validate_phase_j_j4_', 'tests/acceptance/test_phase_j_j4_', 'tests/fixtures/phase_j/j4/')
        j4.require(all(p.startswith(allowed) or p == 'config/test_execution_profiles.json' for p in changed), 'UNAUTHORIZED_PRODUCTION_OR_HISTORICAL_DIFF')
    plans = []
    for cls in j4.CLASSES:
        m = j4.load(ROOT / ('tests/fixtures/phase_j/j4/' + cls.lower() + '.json'))
        p = j4.select_plan(m)
        j4.validate_plan(m, p)
        j4.validate_receipt(m, p, j4.make_receipt(m, p))
        plans.append({'class': cls, 'selected_scenarios': len(p['selected_scenario_ids']), 'required_cells': len(p['required_layers']), 'currently_covered_cells': len(p['currently_covered_layers']), 'coverage_gaps': len(p['planned_or_missing_layers']), 'authorization_gates': p['authorization_gated_layers'], 'disposition': p['gate_disposition']})
    profile = j4.load(ROOT / 'config/test_execution_profiles.json')['profiles']['phase-j-regression-authority']
    j4.require(profile['pytest_paths'] == ['tests/acceptance/test_phase_j_j4_regression_authority.py', 'tests/acceptance/test_phase_j_j3_golden_expected_semantics.py'], 'REGRESSION_PROFILE_DRIFT')
    return {'disposition': 'PHASE_J_J4_REGRESSION_AUTHORITY_VALIDATOR_PASS', 'authority_sha256': j4.file_hash(j4.AUTHORITY), 'change_classes': len(j4.CLASSES), 'scenario_count': len(a['scenario_ids']), 'dimension_count': len(j4.DIMENSIONS), 'safety_core_count': len(a['mandatory_safety_core']), 'layer_count': len(j4.LAYERS), 'mcp_count': len(j4.TOOLS), 'synthetic_plan_calibrations': plans, 'baseline_hashes_verified': len(a['baseline_hashes']), 'market_source_dispatches': 0}


if __name__ == '__main__':
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True, indent=2))
