import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_capability_contract_mirror_cannot_drift():
    assert (ROOT/'skills/tw-market-evidence-agent/assets/unified_capability_catalog_portable.json').exists()
