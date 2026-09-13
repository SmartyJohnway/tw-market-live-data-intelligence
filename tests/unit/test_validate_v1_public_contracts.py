from scripts import validate_v1_public_contracts


def test_v1_public_contract_inventory_matches_runtime() -> None:
    assert validate_v1_public_contracts.main() == 0


def test_readme_validator_rejects_persistent_watchlist_contradiction(tmp_path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "Persistent Watchlists are supported. There is no persistent watchlist.\n",
        encoding="utf-8",
    )
    assert "readme_persistent_watchlist_contradiction" in (
        validate_v1_public_contracts.readme_current_product_truth_failures(readme)
    )
