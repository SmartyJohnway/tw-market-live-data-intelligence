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


def test_readme_validator_accepts_published_rc_status(tmp_path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "\n".join(
            (
                "Persistent Watchlists are supported.",
                "Repository candidate version: `1.0.0-rc.1`.",
                "The latest prerelease is `v1.0.0-rc.1`.",
                "The latest stable GitHub Release remains `v0.1.0`.",
                "Final `v1.0.0` is not released, and Phase G has not started.",
            )
        ),
        encoding="utf-8",
    )
    assert validate_v1_public_contracts.readme_current_product_truth_failures(readme) == []


def test_readme_validator_rejects_stale_prepublication_status(tmp_path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "\n".join(
            (
                "Persistent Watchlists are supported.",
                "Repository candidate version: `1.0.0-rc.1`.",
                "The latest prerelease is `v1.0.0-rc.1`.",
                "The latest stable GitHub Release remains `v0.1.0`.",
                "Final `v1.0.0` is not released, and Phase G has not started.",
                "No RC tag or GitHub prerelease has been created.",
            )
        ),
        encoding="utf-8",
    )
    assert "readme_stale_prepublication_release_status" in (
        validate_v1_public_contracts.readme_current_product_truth_failures(readme)
    )


def test_readme_validator_rejects_missing_final_release_boundary(tmp_path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "Persistent Watchlists are supported. The latest prerelease is v1.0.0-rc.1. "
        "The latest stable GitHub Release remains v0.1.0. Phase G has not started.",
        encoding="utf-8",
    )
    assert "readme_published_rc_release_status_incomplete" in (
        validate_v1_public_contracts.readme_current_product_truth_failures(readme)
    )


def test_readme_validator_rejects_missing_phase_g_boundary(tmp_path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "Persistent Watchlists are supported. The latest prerelease is v1.0.0-rc.1. "
        "The latest stable GitHub Release remains v0.1.0. Final v1.0.0 is not released.",
        encoding="utf-8",
    )
    assert "readme_published_rc_release_status_incomplete" in (
        validate_v1_public_contracts.readme_current_product_truth_failures(readme)
    )


def test_readme_validator_accepts_final_promotion_candidate_status(tmp_path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "\n".join(
            (
                "Persistent Watchlists are supported.",
                "ProductVersion = `1.0.0`.",
                "The latest prerelease is `v1.0.0-rc.1`.",
                "The latest stable GitHub Release remains `v0.1.0`.",
                "Final `v1.0.0` has not yet been published, and Phase G has not started.",
            )
        ),
        encoding="utf-8",
    )
    assert (
        validate_v1_public_contracts.readme_current_product_truth_failures(
            readme, current_product_version="1.0.0"
        )
        == []
    )


def test_readme_validator_rejects_final_promotion_claiming_published(tmp_path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "\n".join(
            (
                "Persistent Watchlists are supported.",
                "ProductVersion = `1.0.0`.",
                "The latest prerelease is `v1.0.0-rc.1`.",
                "The latest stable GitHub Release remains `v0.1.0`.",
                "Final `v1.0.0` is published, and Phase G has not started.",
            )
        ),
        encoding="utf-8",
    )
    assert "readme_final_promotion_release_status_incomplete" in (
        validate_v1_public_contracts.readme_current_product_truth_failures(
            readme, current_product_version="1.0.0"
        )
    )


def test_readme_validator_rejects_final_promotion_missing_rc_provenance(tmp_path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "Persistent Watchlists are supported. ProductVersion = 1.0.0. "
        "The latest stable GitHub Release remains v0.1.0. "
        "Final v1.0.0 has not yet been published, and Phase G has not started.",
        encoding="utf-8",
    )
    assert "readme_final_promotion_release_status_incomplete" in (
        validate_v1_public_contracts.readme_current_product_truth_failures(
            readme, current_product_version="1.0.0"
        )
    )


def test_readme_validator_rejects_final_promotion_missing_phase_g_boundary(tmp_path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "Persistent Watchlists are supported. ProductVersion = 1.0.0. "
        "The latest prerelease is v1.0.0-rc.1. "
        "The latest stable GitHub Release remains v0.1.0. "
        "Final v1.0.0 has not yet been published.",
        encoding="utf-8",
    )
    assert "readme_final_promotion_release_status_incomplete" in (
        validate_v1_public_contracts.readme_current_product_truth_failures(
            readme, current_product_version="1.0.0"
        )
    )
