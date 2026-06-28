import scripts.plan_m5d_frontend_publication as plan
import scripts.simulate_m5d_frontend_publication as sim

def test_m5d_plan_blocks_when_validator_fails(monkeypatch):
    monkeypatch.setattr(plan, 'validate', lambda: [{'code':'bad'}])
    out=plan.plan()
    assert out['status']=='blocked'
    assert out['frontend_public_write'] is False

def test_m5d_simulation_blocks_when_validator_fails(monkeypatch):
    monkeypatch.setattr(sim, 'validate', lambda: [{'code':'bad'}])
    out=sim.simulate()
    assert out['status']=='blocked'
    assert out['publication_performed'] is False
