from __future__ import annotations
import json, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
import pytest
from scripts.m5i_common import validate_authorization, claim_authorization, SOURCE

def auth(**kw):
    base={'schema_version':'m5i_explicit_refresh_authorization.v1','authorization_id':'A1','issued_at_utc':'2026-06-29T00:00:00Z','expires_at_utc':(datetime.now(timezone.utc)+timedelta(days=1)).isoformat().replace('+00:00','Z'),'single_use_id':'S1','single_use':True,'allowed_action':'m5i_explicit_bounded_market_refresh','source':SOURCE,'targets':['0050','00929','2330'],'max_targets':3,'no_frontend_publication':True,'no_production_refresh':True,'no_generated_refresh':True,'no_trading_output':True,'no_full_market_scan':True,'no_polling':True,'operator_acknowledged':True}
    base.update(kw); return base

def test_authorization_accepts_valid_contract():
    assert validate_authorization(auth(), ['0050','00929','2330']) == []

@pytest.mark.parametrize('override,targets,code',[
    ({'source':'BAD'},['0050'],'wrong_source'),
    ({'expires_at_utc':'2000-01-01T00:00:00Z'},['0050'],'expired_authorization'),
    ({'operator_acknowledged':False},['0050'],'missing_operator_acknowledgement'),
    ({'targets':['0050','0050']},['0050','0050'],'duplicate_targets'),
    ({'targets':['*']},['*'],'full_market_or_wildcard_target'),
    ({'targets':['8069']},['8069'],'target_outside_m5f_bounded_scope'),
    ({'single_use':False},['0050'],'single_use_required'),
])
def test_authorization_rejects_invalid_contracts(override, targets, code):
    a=auth(**override); a['targets']=override.get('targets',targets)
    assert code in validate_authorization(a, targets)

def test_check_only_no_network_no_writes():
    r=subprocess.run([sys.executable, str(REPO/'scripts/run_m5i_explicit_bounded_refresh.py'), '--check-only'], cwd=REPO, text=True, capture_output=True, check=True)
    data=json.loads(r.stdout); assert data['network_calls'] is False and data['artifact_writes'] is False

def test_execute_requires_authorization():
    r=subprocess.run([sys.executable, str(REPO/'scripts/run_m5i_explicit_bounded_refresh.py'), '--execute-refresh', '--source', 'TWSE_OpenAPI', '--targets', '0050'], cwd=REPO, text=True, capture_output=True)
    assert r.returncode != 0

def test_parse_twse_rows_price_semantics():
    import scripts.run_m5i_explicit_bounded_refresh as ref
    targets = ['0050', '00929', '2330', '8069']

    # 0050 valid
    # 00929 missing close price but has TradeVolume (should fail target)
    # 2330 unparsable close
    # 8069 completely missing

    data = [
        {'Code': '0050', 'ClosingPrice': '150.0'},
        {'Code': '00929', 'TradeVolume': '5000'},
        {'Code': '2330', 'ClosingPrice': 'NOT_A_NUMBER'}
    ]

    rows, failures = ref.parse_twse_rows(data, targets, '2026-06-29T00:00:00Z')

    # Only 0050 should be parsed successfully
    assert len(rows) == 1
    assert rows[0]['symbol'] == '0050'
    assert rows[0]['price_like_value'] == 150.0

    # 3 failures should occur
    failed_syms = {f['symbol']: f['status'] for f in failures}
    assert '00929' in failed_syms
    assert failed_syms['00929'] == 'missing_close_price'

    assert '2330' in failed_syms
    assert failed_syms['2330'] == 'unparsable_close_price'

    assert '8069' in failed_syms
    assert failed_syms['8069'] == 'missing_from_source'

def test_single_use_claim_atomic(tmp_path, monkeypatch):
    import scripts.m5i_common as c
    monkeypatch.setattr(c,'REPO',tmp_path)
    a=auth(authorization_id='A2',single_use_id='S2',targets=['0050'])
    p=claim_authorization(a); assert p.exists()
    with pytest.raises(FileExistsError): claim_authorization(a)

def test_promotion_wrapper_failure_leaves_canonical_untouched(tmp_path, monkeypatch):
    import scripts.m5i_common as c
    monkeypatch.setattr(c, 'REPO', tmp_path)

    # Mock candidate validation failure
    canonical = tmp_path/'research/staging/m5f/m5f_canonical_market_context_01'
    canonical.mkdir(parents=True)
    (canonical/'test.txt').write_text('original')

    candidate = tmp_path/'candidate'
    candidate.mkdir()

    res = c.promote_m5i_candidate_to_m5f(candidate)
    assert res['status'] == 'failed'
    assert res['stage'] == 'temp_package_build_or_validate'
    assert (canonical/'test.txt').read_text() == 'original'

def test_promotion_wrapper_rolls_back_on_final_replace_failure(tmp_path, monkeypatch):
    import scripts.m5i_common as c
    monkeypatch.setattr(c, 'REPO', tmp_path)

    canonical = tmp_path/'research/staging/m5f/m5f_canonical_market_context_01'
    canonical.mkdir(parents=True)
    (canonical/'test.txt').write_text('original')

    # We force `shutil.copytree(temp_dir, canonical_dir)` to fail
    import shutil
    orig_copytree = shutil.copytree
    def failing_copytree(src, dst, **kw):
        if 'm5i_promote_' in str(src):
            raise OSError("Injected copy failure")
        return orig_copytree(src, dst, **kw)

    monkeypatch.setattr(shutil, 'copytree', failing_copytree)

    # Mock a valid candidate
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
    import build_m5f_canonical_market_context_package as bld
    import validate_m5f_canonical_market_context_package as val
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
    import build_m5f_canonical_market_context_package as bld
    import validate_m5f_canonical_market_context_package as val
    monkeypatch.setattr(bld, 'write_package', lambda c, t: (t/'built.txt').write_text('built'))
    monkeypatch.setattr(val, 'validate_package', lambda p: {'status':'passed'})

    res = c.promote_m5i_candidate_to_m5f(tmp_path/'candidate')
    assert res['status'] == 'failed'
    assert res['stage'] == 'final_replace'
    assert res['rollback'] == 'successful'
    assert (canonical/'test.txt').read_text() == 'original'

def test_promotion_wrapper_rolls_back_on_post_promotion_validation_failure(tmp_path, monkeypatch):
    import scripts.m5i_common as c
    monkeypatch.setattr(c, 'REPO', tmp_path)

    canonical = tmp_path/'research/staging/m5f/m5f_canonical_market_context_01'
    canonical.mkdir(parents=True)
    (canonical/'test.txt').write_text('original')

    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
    import build_m5f_canonical_market_context_package as bld
    import validate_m5f_canonical_market_context_package as val
    monkeypatch.setattr(bld, 'write_package', lambda c, t: (t/'built.txt').write_text('built'))

    calls = []
    def failing_validation(p):
        calls.append(p)
        if 'm5f_canonical_market_context_01' in str(p):
            raise ValueError("Injected validation failure")
        return {'status':'passed'}

    monkeypatch.setattr(val, 'validate_package', failing_validation)

    res = c.promote_m5i_candidate_to_m5f(tmp_path/'candidate')
    assert res['status'] == 'failed'
    assert res['stage'] == 'post_promotion_validation'
    assert res['rollback'] == 'successful'
    assert (canonical/'test.txt').read_text() == 'original'
