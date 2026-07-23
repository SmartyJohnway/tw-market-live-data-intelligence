import copy
import pytest
from scripts.m8r_05b_01.canonical import *


def test_canonical_json_and_hash_are_order_independent():
    assert canonical_json({'b': 1, 'a': '台'}) == '{"a":"台","b":1}'
    assert sha256_json({'b': 1, 'a': '台'}) == sha256_json({'a': '台', 'b': 1})


def test_nan_and_unordered_target_errors_fail_closed():
    with pytest.raises(ValueError): canonical_json({'x': float('nan')})
    with pytest.raises(ValueError): canonical_target_ids(['TWSE:2330', 'TWSE:2330'])


def test_plan_id_derives_from_exact_hash():
    digest, ident = plan_hash_and_id({'schema_version': 'x', 'operations': []})
    assert ident == 'umeop-v1-' + digest[:20]


def test_operation_and_batch_identity_change_with_semantics():
    scope = {'capability_id': 'identity', 'canonical_target_ids': ['TWSE:2330']}
    assert operation_id(scope) == operation_id(dict(reversed(list(scope.items()))))
    assert operation_id(scope) != operation_id({**scope, 'capability_id': 'recent_performance'})
    assert batch_group_id(scope) != batch_group_id({**scope, 'market': 'TWSE'})


def test_warning_order_canonicalizes_targets_without_mutation_or_display_text():
    warnings = [
        {'code': 'a', 'capability_id': 'x', 'canonical_target_ids': ['TWSE:2330', 'TPEX:6488'], 'severity': 'warning', 'omission_reason': 'a', 'display_text': 'z'},
        {'code': 'a', 'capability_id': 'x', 'canonical_target_ids': ['TPEX:6488', 'TWSE:2330'], 'severity': 'warning', 'omission_reason': 'a', 'display_text': 'different'},
    ]
    original = copy.deepcopy(warnings)
    ordered = canonical_warning_order(warnings)
    assert warnings == original
    assert [item['canonical_target_ids'] for item in ordered] == [['TPEX:6488', 'TWSE:2330']] * 2
    assert canonical_warning_order([warnings[0]])[0]['canonical_target_ids'] == canonical_warning_order([warnings[1]])[0]['canonical_target_ids']


@pytest.mark.parametrize('targets', [['TWSE:2330', 'TWSE:2330'], ['TWSE:2330', 1]])
def test_warning_target_normalization_fails_closed(targets):
    with pytest.raises(ValueError):
        canonical_warning_order([{'code': 'a', 'capability_id': 'x', 'canonical_target_ids': targets, 'severity': 'warning', 'omission_reason': 'a'}])


def _operation(operation_id_value, capability_id, market, target):
    return {'operation_id': operation_id_value, 'capability_id': capability_id, 'market': market, 'canonical_target_ids': [target] if target else [], 'parameters': {}, 'executor_id': 'adapter'}


def test_operation_order_uses_external_context_and_keeps_schema_shape():
    operations = [_operation('op-tpex', 'current_observation', 'TPEX', 'TPEX:6488'), _operation('op-twse', 'current_observation', 'TWSE', 'TWSE:2330')]
    original = copy.deepcopy(operations)
    ordered = canonical_operation_order(operations, capability_order_by_id={'current_observation': 0}, batch_key_by_operation_id={'op-tpex': 'b', 'op-twse': 'b'})
    assert operations == original
    assert [item['market'] for item in ordered] == ['TWSE', 'TPEX']
    assert all('capability_order' not in item and 'batch_key' not in item for item in ordered)


def test_operation_permutations_and_taifex_order_are_stable():
    operations = [_operation('taifex', 'current_observation', 'TAIFEX', 'TAIFEX:TX'), _operation('tpex', 'current_observation', 'TPEX', 'TPEX:6488'), _operation('twse', 'current_observation', 'TWSE', 'TWSE:2330')]
    context = {'capability_order_by_id': {'current_observation': 0}, 'batch_key_by_operation_id': {item['operation_id']: 'b' for item in operations}}
    assert [item['market'] for item in canonical_operation_order(list(reversed(operations)), **context)] == ['TWSE', 'TPEX', 'TAIFEX']


@pytest.mark.parametrize('operation, context, error', [
    (_operation('one', 'unknown', 'TWSE', 'TWSE:2330'), {'capability_order_by_id': {}, 'batch_key_by_operation_id': {'one': 'b'}}, 'capability_order_unknown'),
    (_operation('one', 'identity', 'OTHER', 'TWSE:2330'), {'capability_order_by_id': {'identity': 0}, 'batch_key_by_operation_id': {'one': 'b'}}, 'market_unknown'),
    (_operation('one', 'identity', None, None), {'capability_order_by_id': {'identity': 0}, 'batch_key_by_operation_id': {'one': 'b'}}, 'cross_market_derived_rule_violation'),
])
def test_operation_order_fails_closed_for_unknown_context(operation, context, error):
    with pytest.raises(ValueError, match=error):
        canonical_operation_order([operation], **context)


def test_duplicate_operation_ids_fail_closed():
    operation = _operation('same', 'identity', 'TWSE', 'TWSE:2330')
    with pytest.raises(ValueError, match='operation_id_duplicate'):
        canonical_operation_order([operation, dict(operation)], capability_order_by_id={'identity': 0}, batch_key_by_operation_id={'same': 'b'})
