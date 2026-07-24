from scripts.m8r_05b_02.authorization import build_execution_authorization
from scripts.m8r_05b_02.consumption_binding import build_consumption_binding
from tests.unit.test_m8r_05b_02_authorization import plan,decision
def test_binding_deterministic(): assert build_consumption_binding(build_execution_authorization(plan(),decision()))==build_consumption_binding(build_execution_authorization(plan(),decision()))
