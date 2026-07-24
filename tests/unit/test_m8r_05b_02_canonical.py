from scripts.m8r_05b_02.canonical import canonical_json,authorization_identity
def test_canonical(): assert canonical_json({'b':1,'a':'台'})=='{"a":"台","b":1}' and authorization_identity({'a':1})==authorization_identity({'a':1})
