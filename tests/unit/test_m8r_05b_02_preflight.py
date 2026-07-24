from scripts.m8r_05b_02.preflight import evaluate_authorization_preflight
# exercised via authorization suite; module intentionally has no ambient clock.
def test_importable(): assert callable(evaluate_authorization_preflight)
