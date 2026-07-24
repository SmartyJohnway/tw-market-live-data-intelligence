import pytest
from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding,evaluate_consumption_preflight
from tests.unit.test_m8r_05b_02_authorization import plan,decision
def test_states():
 a=build_execution_authorization(plan(),decision());b=build_consumption_binding(a);assert evaluate_consumption_preflight(a,plan(),b,'2026-07-23T00:30:00Z',{'authorization_id':a['authorization_id'],'state':'unused'})['status']=='ready_for_controlled_consumption'
 with pytest.raises(Exception) as e:evaluate_consumption_preflight(a,plan(),b,'2026-07-23T00:30:00Z',None)
 assert e.value.code=='consumption_record_missing'
