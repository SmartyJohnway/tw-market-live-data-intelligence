from pathlib import Path


def test_browser_e2e_dependency_is_exactly_pinned() -> None:
    lines = (Path(__file__).resolve().parents[2] / "requirements-browser-e2e.txt").read_text(encoding="utf-8").splitlines()
    pins = [line for line in lines if line.startswith("playwright")]
    assert pins == ["playwright==1.55.0"]
