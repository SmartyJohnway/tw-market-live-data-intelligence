import copy
import json
import pytest
from scripts.validate_phase_j_b03_c0_closure import RECORD, PREFLIGHT, S3, A26, ROUTING, validate, validate_record

def _load(p): return json.loads(p.read_text(encoding="utf-8"))

def inputs(): return [_load(RECORD), _load(PREFLIGHT), _load(S3), _load(A26), _load(ROUTING)]

def test_current_c0_closure():
    assert validate() == {"status":"PASS","j_b03":"CLOSED","remaining_blocker":"J-B04","mcp":6,"market_gets":0}

@pytest.mark.parametrize("issue", ["H0-SRC-01E", "H0-SRC-02"])
def test_open_h1_issue_cannot_be_silently_closed(issue):
    vals=inputs(); vals[0]["issue_disposition"][issue]["state"]="CLOSED"
    with pytest.raises(AssertionError): validate_record(*vals)

def test_j_b04_must_remain_only_blocker():
    vals=inputs(); vals[0]["phase_j_readiness"]["remaining_entry_blockers"]=[]
    with pytest.raises(AssertionError): validate_record(*vals)

def test_phase_j_cannot_start_in_c0():
    vals=inputs(); vals[0]["phase_j_readiness"]["phase_j_started"]=True
    with pytest.raises(AssertionError): validate_record(*vals)

def test_full_h1_cannot_be_reclassified_as_c0_requirement():
    vals=inputs(); vals[0]["product_exit_basis"]["full_h1_required_for_j_b03_closure"]=True
    with pytest.raises(AssertionError): validate_record(*vals)
