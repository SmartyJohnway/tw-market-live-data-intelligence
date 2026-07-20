import json, os

def test_inventory_integrity():
    with open('docs/reviews/m8r_05a_f1_ai_facing_artifact_inventory.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    assert len(data) >= 50
    canonical_count = 0
    for item in data:
        assert 'path' in item
        assert 'blob_sha' in item
        assert 'evidence' in item
        assert 'classification' in item
        assert os.path.exists(item['path'])
        if item['classification'] == 'CURRENT_CANONICAL':
            canonical_count += 1
    assert canonical_count >= 5, 'Must have at least 4 schemas and 1 catalog instance as canonical'

def test_matrix_integrity():
    with open('docs/reviews/m8r_05a_f1_policy_and_contract_conflict_matrix.json', 'r', encoding='utf-8') as f:
        cdata = json.load(f)
    assert len(cdata['recommendation_policy_conflicts']) == 2
    assert len(cdata) >= 6 # At least 6 conflict categories
    with open('docs/reviews/m8r_05a_f1_source_of_truth_and_compatibility_matrix.json', 'r', encoding='utf-8') as f:
        sdata = json.load(f)
    assert len(sdata['hierarchies']['Internal Runtime Authority']) >= 2
    assert any('m8_source_capability_registry' in x['artifact'] for x in sdata['hierarchies']['Internal Runtime Authority'])

