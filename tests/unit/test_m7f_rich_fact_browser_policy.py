from pathlib import Path


POLICY = Path("docs/protocol/M7F_RICH_FACT_BROWSER_POLICY.md")
CONTRACT = Path("docs/protocol/M7F_RICH_FACT_EXPOSURE_CONTRACT.md")
SCHEMA = Path("docs/protocol/M7F_RICH_FACT_DISPLAY_SCHEMA.md")


def test_m7f_policy_documents_exist():
    assert POLICY.exists()
    assert CONTRACT.exists()
    assert SCHEMA.exists()


def test_m7f_policy_declares_rich_not_summary_only_stance():
    text = POLICY.read_text(encoding="utf-8").lower()
    for phrase in [
        "not summary-only",
        "project-validated rich facts",
        "official per-field documentation is not required",
        "provenance",
        "confidence",
        "caveats",
        "raw endpoint payload exposure",
        "trading advice",
    ]:
        assert phrase in text


def test_m7f_exposure_contract_required_classes():
    text = CONTRACT.read_text(encoding="utf-8")
    for exposure_class in [
        "operator_display_allowed",
        "ai_handoff_allowed",
        "operator_only",
        "caveated_display_allowed",
        "structured_display_candidate",
        "raw_forbidden",
        "future_review_required",
    ]:
        assert exposure_class in text
