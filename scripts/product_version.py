"""Tracked product-version authority that also works from source archives."""
from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_PATH = ROOT / "VERSION"
_SEMVER = re.compile(
    r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)


class ProductVersionError(RuntimeError):
    """The tracked product version cannot safely be used."""


def product_version(*, version_path: Path = VERSION_PATH) -> str:
    """Read and validate the one tracked product SemVer authority."""
    try:
        value = version_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise ProductVersionError("product_version_unavailable") from exc
    if not _SEMVER.fullmatch(value):
        raise ProductVersionError("product_version_invalid")
    return value
