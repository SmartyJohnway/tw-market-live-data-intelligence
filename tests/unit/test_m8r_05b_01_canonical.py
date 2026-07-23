import pytest
from scripts.m8r_05b_01.canonical import *

def test_canonical_json_and_hash_are_order_independent():
 assert canonical_json({'b':1,'a':'台'}) == '{"a":"台","b":1}'
 assert sha256_json({'b':1,'a':'台'}) == sha256_json({'a':'台','b':1})
def test_nan_and_unordered_target_errors_fail_closed():
 with pytest.raises(ValueError): canonical_json({'x':float('nan')})
 with pytest.raises(ValueError): canonical_target_ids(['TWSE:2330','TWSE:2330'])
def test_plan_id_derives_from_exact_hash():
 digest, ident=plan_hash_and_id({'schema_version':'x','operations':[]})
 assert ident == 'umeop-v1-'+digest[:20]
def test_operation_and_batch_identity_change_with_semantics():
 s={'capability_id':'identity','canonical_target_ids':['TWSE:2330']}
 assert operation_id(s) == operation_id(dict(reversed(list(s.items()))))
 assert operation_id(s) != operation_id({**s,'capability_id':'recent_performance'})
 assert batch_group_id(s) != batch_group_id({**s,'market':'TWSE'})
def test_operation_order_uses_semantic_market_and_targets():
 ops=[{'capability_order':1,'market':'TPEX','canonical_target_ids':['TPEX:6488'],'parameters':{},'executor_id':'b','operation_id':'z'}, {'capability_order':1,'market':'TWSE','canonical_target_ids':['TWSE:2330'],'parameters':{},'executor_id':'a','operation_id':'a'}]
 assert [x['market'] for x in canonical_operation_order(ops)] == ['TWSE','TPEX']
def test_warning_order_excludes_display_text_from_sort_semantics():
 ws=[{'code':'b','capability_id':'x','canonical_target_ids':[],'severity':'warning','omission_reason':'b','display_text':'z'}, {'code':'a','capability_id':'x','canonical_target_ids':[],'severity':'warning','omission_reason':'a','display_text':'y'}]
 assert [x['code'] for x in canonical_warning_order(ws)] == ['a','b']
