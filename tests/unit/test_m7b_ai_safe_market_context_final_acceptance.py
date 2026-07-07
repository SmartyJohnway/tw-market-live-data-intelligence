import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/protocol/M7B_AI_SAFE_MARKET_CONTEXT_FINAL_ACCEPTANCE.md"
INVENTORY = ROOT / "docs/data_capabilities/twse_mis_rich_field_inventory.json"

CAVEATS = [
    "no official public TWSE MIS API field dictionary",
    "no realtime SLA",
    "quantity units remain unverified",
    "displayed depth remains displayed-depth snapshot only",
    "not full order book",
    "not true liquidity",
    "not support/resistance",
    "not trading signal",
    "not recommendation",
    "odd-lot semantics not fully runtime-integrated",
]

FORBIDDEN_POSITIVE = [
    "buy opportunity",
    "sell pressure",
    "support level",
    "resistance level",
    "target price estimate",
    "main force accumulation",
    "liquidity signal",
    "confirmed trend",
    "realtime feed",
    "official api definition validated",
    "verified quantity unit available",
]


def test_final_acceptance_doc_exists_status_caveats_and_no_go_confirmations():
    text = DOC.read_text(encoding="utf-8")
    assert "Status:\n- pass_with_caveats" in text
    for task in ["M7B-00", "M7B-01", "M7B-02", "M7B-03", "M7B-04", "M7B-05", "M7B-06"]:
        assert task in text
    for caveat in CAVEATS:
        assert caveat in text
    for phrase in ["no live probe", "no new probe output committed", "no latest_summary.json committed", "no cookies/headers/session tokens committed"]:
        assert phrase in text
    assert "M7C-DETERMINISTIC-METRICS-LAYER" in text
    assert "change_percent" in text
    assert "displayed_spread" in text
    assert "later M8 preflight" in text
    assert "M7C-AI-MARKET-CONTEXT-MULTISOURCE-EXPANSION-OR-SOURCE-FRESHNESS-GOVERNANCE" not in text


def test_forbidden_positive_language_absent_from_m7b_artifacts():
    paths = [
        DOC,
        ROOT / "docs/protocol/M7B_AI_SAFE_MARKET_CONTEXT_PROJECTION_POLICY.md",
        INVENTORY,
        ROOT / "scripts/observation_contract.py",
        ROOT / "scripts/m5k_common.py",
    ]
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in paths)
    for phrase in FORBIDDEN_POSITIVE:
        assert phrase not in text


def test_no_latest_summary_or_new_probe_output_committed_in_current_branch():
    changed = subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=ROOT, text=True).splitlines()
    assert "latest_summary.json" not in changed
    assert not [p for p in changed if p.startswith("research/probe_runs/")]


def test_inventory_final_m7b_metadata():
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    m7b = inv["rich_observation_contract"]["m7b_ai_safe_market_context_projection"]
    assert m7b["completed_tasks"] == ["M7B-00", "M7B-01", "M7B-02", "M7B-03", "M7B-04", "M7B-05", "M7B-06"]
    assert m7b["controlled_exposure_enabled"] is True
    assert m7b["runtime_exposure_enabled"] is True
    assert m7b["runtime_populated"] is True
    assert m7b["runtime_behavior_changed"] is True
    assert m7b["runtime_observation_behavior_changed"] is False
    assert m7b["conversation_context_changed"] is True
    assert m7b["frontend_changed"] is False
    assert m7b["source_health_changed"] is False
    assert m7b["latest_observation_changed"] is False
    assert m7b["safe_for_ai_context"] is True
    assert m7b["m7a_rich_facts_safe_for_ai_context"] is False
    assert m7b["raw_rich_facts_exposed"] is False
    assert m7b["full_ladder_exposed"] is False
    assert m7b["trading_signal"] is False
    assert m7b["recommendation"] is False
    assert m7b["final_acceptance_status"] == "pass_with_caveats"
