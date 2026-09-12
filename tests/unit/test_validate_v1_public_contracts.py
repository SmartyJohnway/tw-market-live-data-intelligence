from scripts import validate_v1_public_contracts


def test_v1_public_contract_inventory_matches_runtime() -> None:
    assert validate_v1_public_contracts.main() == 0
