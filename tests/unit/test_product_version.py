from pathlib import Path

import pytest

from scripts.product_version import ProductVersionError, product_version


def test_product_version_is_tracked_rc_candidate_authority():
    assert product_version() == "1.0.0-rc.1"


@pytest.mark.parametrize("value", ("", "v1.0.0", "1.0", "1.0.0\nextra"))
def test_product_version_fails_closed_for_invalid_semver(tmp_path: Path, value: str):
    path = tmp_path / "VERSION"
    path.write_text(value, encoding="utf-8")
    with pytest.raises(ProductVersionError, match="product_version_invalid"):
        product_version(version_path=path)
