from __future__ import annotations
import json, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
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
    r=subprocess.run([sys.executable,'scripts/run_m5i_explicit_bounded_refresh.py','--check-only'],text=True,capture_output=True,check=True)
    data=json.loads(r.stdout); assert data['network_calls'] is False and data['artifact_writes'] is False

def test_execute_requires_authorization():
    r=subprocess.run([sys.executable,'scripts/run_m5i_explicit_bounded_refresh.py','--execute-refresh','--source','TWSE_OpenAPI','--targets','0050'],text=True,capture_output=True)
    assert r.returncode != 0

def test_single_use_claim_atomic(tmp_path, monkeypatch):
    import scripts.m5i_common as c
    monkeypatch.setattr(c,'REPO',tmp_path)
    a=auth(authorization_id='A2',single_use_id='S2',targets=['0050'])
    p=claim_authorization(a); assert p.exists()
    with pytest.raises(FileExistsError): claim_authorization(a)
