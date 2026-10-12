"""Network-free regression protection for the reused browser/overlay boundaries."""
import copy
import json
from pathlib import Path
import pytest
from scripts.run_v1_workbench_browser_e2e import guard_local_browser_context
from scripts.validate_phase_j_j2_r1_workbench_headless_completion import derive, MATRIX, ROOT
from tests.helpers.phase_j_j2_r1_browser import SCENARIOS, request_for

class Context:
    def route(self, pattern, handler): self.handler=handler
class Request:
    def __init__(self,url): self.url=url; self.method='GET'
class Route:
    def __init__(self,url): self.request=Request(url);self.allowed=False;self.aborted=False
    def continue_(self): self.allowed=True
    def abort(self,reason): self.aborted=True

def test_browser_guard_permits_only_exact_local_application_origin():
    context=Context();ledger=guard_local_browser_context(context,'http://127.0.0.1:1234')
    local=Route('http://127.0.0.1:1234/workbench/');context.handler(local)
    assert local.allowed
    for url in ('https://www.twse.com.tw/','http://127.0.0.1:9999/','http://example.invalid/'):
        external=Route(url);context.handler(external);assert external.aborted and not external.allowed
    assert len(ledger['local_requests'])==1 and len(ledger['external_requests'])==3

def promotion(kind='workbench_test'):
    return {'scenario_id':'J1-01','layer':'workbench','baseline_status':'PLANNED','new_status':'COVERED_EXISTING','introduced_by_tranche':'PHASE_J_J2_R1','evidence_refs':[{'ref':'tests/acceptance/test_phase_j_j2_r1_workbench_headless.py::test_scenario_real_workbench_service_mcp[J1-01]','kind':kind,'scenario_match':'actual headless user path/DOM'}]}

def test_effective_matrix_is_derived_only_from_accepted_j1():
    baseline=json.loads((ROOT/MATRIX).read_text());original=copy.deepcopy(baseline)
    effective=derive(baseline,{'promotions':[promotion()]})
    assert baseline==original
    assert effective['scenarios'][0]['layers']['workbench']['status']=='COVERED_EXISTING'
    assert effective['scenarios'][0]['layers']['bounded_live']==baseline['scenarios'][0]['layers']['bounded_live']

@pytest.mark.parametrize('kind',['service_test','unit_test','contract_authority','routing_authority'])
def test_workbench_coverage_cannot_be_laundered_from_other_layers(kind):
    with pytest.raises(ValueError,match='layer evidence laundering'):
        derive(json.loads((ROOT/MATRIX).read_text()),{'promotions':[promotion(kind)]})

def test_exact_17_scenarios_and_request_shapes():
    assert len(SCENARIOS)==len(set(SCENARIOS))==17
    assert request_for('J1-10')['data_needs'][0]['type']=='financial_statements'
    assert len(request_for('J1-27')['targets'])==51
    assert request_for('J1-24')['targets'][0]['input']=='3333'
