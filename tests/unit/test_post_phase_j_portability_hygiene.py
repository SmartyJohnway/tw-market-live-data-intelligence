from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_installation_local_data_is_globally_ignored():
    lines = {
        line.strip()
        for line in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert "data/" in lines
    assert not any(line.startswith("!data/") for line in lines)


def test_hygiene_policy_keeps_phase_j_runtime_out_of_product_contract():
    text = (ROOT / "docs/operations/POST_PHASE_J_PORTABILITY_AND_RUNTIME_HYGIENE.md").read_text(encoding="utf-8")
    assert "Third-party acceptance distribution" in text
    assert "741.45 MiB" in text
    assert "Prior qualified releases are not disposable cache" in text
    assert "Historical governance evidence may retain the exact absolute paths" in text
