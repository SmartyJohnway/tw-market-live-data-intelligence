import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT/'docs/ai/m8_ai_capability_contract.json'

def test_legacy_contract_is_archived():
    contract = json.load(open(CONTRACT_PATH, encoding='utf-8'))
    assert "_archive_status" in contract
    assert contract["_archive_status"]["status"] == "archived"
    assert contract["_archive_status"]["superseded_by"] == "M8R-05A"
