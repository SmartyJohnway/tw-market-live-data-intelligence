import json, os, re

VALID_CLASSIFICATIONS = {'REWRITE_REQUIRED', 'RETAIN_AND_REINTERPRET', 'CURRENT_CANONICAL', 'RETAIN_AND_STRENGTHEN', 'COMPATIBILITY_ONLY_LEGACY'}

def test_inventory_integrity():
    with open('docs/reviews/m8r_05a_f1_ai_facing_artifact_inventory.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert len(data) >= 65
    canonical_count = 0
    for item in data:
        assert 'path' in item and os.path.exists(item['path'])
        assert 'blob_sha' in item and len(item['blob_sha']) == 40 and re.match(r'^[0-9a-f]+$', item['blob_sha'])
        assert 'evidence' in item
        assert item['classification'] in VALID_CLASSIFICATIONS
        if item['classification'] == 'CURRENT_CANONICAL':
            canonical_count += 1
        if any(x in item['path'] for x in ['m8r_03c', 'm8r_03d', 'm8r_03e']):
            if 'test' not in item['path'] and 'fixture' not in item['path']:
                assert item['classification'] == 'RETAIN_AND_STRENGTHEN', f"{item['path']} must not be legacy"
    assert canonical_count >= 6, 'Must have at least 6 canonical items'

def test_matrix_integrity():
    with open('docs/reviews/m8r_05a_f1_policy_and_contract_conflict_matrix.json', 'r', encoding='utf-8') as f:
        cdata = json.load(f)
    assert len(cdata['recommendation_policy_conflicts']) == 2
    assert len(cdata) >= 6
    with open('docs/reviews/m8r_05a_f1_source_of_truth_and_compatibility_matrix.json', 'r', encoding='utf-8') as f:
        sdata = json.load(f)
    assert any('m8_source_capability_registry' in x['artifact'] for x in sdata['hierarchies']['Internal Runtime Authority'])
    assert any('unified_market_evidence_capability_catalog.v1.json' in x['artifact'] for x in sdata['hierarchies']['AI-facing Contract Authority'])

def test_migration_plan_coverage():
    with open('docs/roadmap/M8R_05A_F1_AI_GUIDE_SKILL_AND_CONTRACT_REALIGNMENT_MIGRATION_PLAN.md', 'r', encoding='utf-8') as f:
        text = f.read()
    assert 'docs/ai_safety_policy.md' in text
    assert 'docs/agent_usage_guide.md' in text
    assert 'skills/tw-market-evidence-agent/SKILL.md' in text
    assert 'frontend/readonly-preview/M5KLocalAIWorkbench.html' in text
    assert 'server/main.py' in text

