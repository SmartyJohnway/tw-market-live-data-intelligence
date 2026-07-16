from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_capability_contract_mirror_cannot_drift():
    assert (ROOT/'docs/ai/m8_ai_capability_contract.json').read_bytes()==(ROOT/'skills/tw-market-evidence-agent/assets/m8_ai_capability_contract.json').read_bytes()
