from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_four_file_governance_front_door_exists_and_is_current() -> None:
    for path in ("PROJECT.md", "ROADMAP.md", "HANDOFF.md", "AGENTS.md"):
        assert (ROOT / path).is_file(), path

    project = _text("PROJECT.md")
    roadmap = _text("ROADMAP.md")
    handoff = _text("HANDOFF.md")
    agents = _text("AGENTS.md")

    assert "unified_market_evidence_request.v3" in project
    assert "Roadmap V3.2" in roadmap
    assert "Phase I — Cross-Market & Optional Context" in roadmap
    assert 'status_reconciled_through: "H-ACT-V3 promotion; Phase I not started"' in roadmap
    assert "Phase I — Cross-Market & Optional Context" in roadmap
    assert "Phase I                      NOT STARTED" in handoff
    assert "Do not enter Phase I implementation" in agents


def test_current_front_doors_do_not_regress_to_v2_preferred_or_old_roadmap() -> None:
    paths = (
        "README.md",
        "README.zh-TW.md",
        "PROJECT.md",
        "HANDOFF.md",
        "docs/INDEX.md",
        "docs/operator/QUICK_START.md",
        "docs/operator/LOCAL_WORKBENCH.md",
        "docs/operator/MODE_ABC_WALKTHROUGH.md",
        "docs/reference/MCP_REFERENCE.md",
        "docs/reference/CAPABILITY_MATRIX.md",
        "docs/architecture/PRODUCT_ARCHITECTURE.md",
    )
    joined = "\n".join(_text(path) for path in paths).casefold()

    assert "request v2 is preferred" not in joined
    assert "request v2 是現行偏好契約" not in joined
    assert "phase h — long-running operation and automation" not in joined
    assert "phase i — minimal quote interpretation enrichment" not in joined

    assert "request v3" in joined
    assert "exactly six" in joined or "六個" in joined


def test_current_catalog_metadata_matches_post_promotion_truth() -> None:
    catalog = json.loads(
        _text("docs/data_capabilities/unified_market_evidence_capability_catalog.v3.json")
    )
    versions = catalog["contract_versions"]
    assert versions["preferred_request_schema_version"] == "unified_market_evidence_request.v3"
    assert versions["emitted_result_schema_version"] == "unified_market_evidence_result.v3"

    capabilities = {
        item["capability_id"]: item for item in catalog["data_need_capabilities"]
    }
    h1_text = " ".join(capabilities["trading_status_context"]["known_limitations"])
    h2_text = " ".join(capabilities["corporate_action_context"]["known_limitations"])

    assert "V2 remains the preferred" not in h1_text
    assert "V3 is the preferred production request/result authority" in h1_text
    assert "V3 contract candidate only" not in h2_text
    assert "no H2 corporate-action route has been activated" in h2_text


def test_roadmap_archive_boundary_is_explicit_and_compatibility_paths_remain() -> None:
    canonical = ROOT / "ROADMAP.md"
    assert canonical.is_file()

    moved = (
        "M8_POST_M8C_REPOSITORY_STATE_INVENTORY.md",
        "M8_POST_M8C_ROADMAP_CONFLICT_MATRIX.md",
        "M8_REMEDIATION_AND_CLEANUP_PLAN.md",
        "NEXT_BUNDLE_ROADMAP_AFTER_M4_OMEGA.md",
    )
    for name in moved:
        assert not (ROOT / "docs/roadmap" / name).exists(), name
        assert (ROOT / "docs/archive/roadmap" / name).is_file(), name

    for name in (
        "M8_POST_M8C_REVISED_ROADMAP.md",
        "M8R_05A_F1_AI_GUIDE_SKILL_AND_CONTRACT_REALIGNMENT_MIGRATION_PLAN.md",
    ):
        assert (ROOT / "docs/roadmap" / name).is_file(), name

    roadmap_index = _text("docs/roadmap/README.md")
    assert "../../ROADMAP.md" in roadmap_index
    assert "historical" in roadmap_index.casefold()


def test_historical_release_snapshot_is_not_presented_as_current_state() -> None:
    text = _text("docs/release/V1_RELEASE.md")
    assert "Historical release snapshot" in text
    assert "historical release provenance" in text
    assert "PROJECT.md" in text
