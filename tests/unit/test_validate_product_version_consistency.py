from scripts import validate_product_version_consistency


def test_product_version_consistency_gate() -> None:
    assert validate_product_version_consistency.main() == 0
