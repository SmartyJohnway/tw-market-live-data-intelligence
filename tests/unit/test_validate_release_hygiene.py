from pathlib import Path

from scripts import validate_release_hygiene as hygiene


def _tracked(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*") if path.is_file())


def test_hygiene_reports_missing_relative_markdown_link(tmp_path, monkeypatch) -> None:
    (tmp_path / "README.md").write_text("[missing](missing.md)\n", encoding="utf-8")
    monkeypatch.setattr(hygiene, "tracked_files", lambda root: _tracked(root))
    monkeypatch.setattr(hygiene, "CURRENT_DOCUMENTS", ("README.md",))
    assert hygiene.check_markdown_links(tmp_path) == ["README.md -> missing.md"]


def test_hygiene_detects_high_confidence_secret_without_printing_value(tmp_path, monkeypatch) -> None:
    # Construct the synthetic value at runtime so the hygiene scanner does not
    # flag this test source itself as a committed credential-shaped string.
    fake_access_key = "AKIA" + "1234567890ABCDEF"
    (tmp_path / "source.txt").write_text(f"token={fake_access_key}\n", encoding="utf-8")
    monkeypatch.setattr(hygiene, "tracked_files", lambda root: _tracked(root))
    assert hygiene.check_high_confidence_secrets(tmp_path) == ["source.txt"]
