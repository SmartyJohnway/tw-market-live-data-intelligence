from pathlib import Path
import shutil

from scripts.m8r_taifex_current_contract_resolver import FixtureUniverseProvider
from scripts.run_m8r_conversational_derivatives_context import conversation_resolution_projection, run, safe_root


def test_conversation_resolution_projection_is_ai_safe():
    record = {"original_user_text":"現在台指選擇權怎麼樣？", "resolved_exact_targets":[{"product":"TXO","expiry":"202607W4","strike":"45000","call_put":"C"}], "assumptions":[{"code":"call_put_policy","value":"both"}], "reference_observation":{"reference_source":"fixture","reference_value":"45000"}, "reresolution_count":1}
    out = conversation_resolution_projection(record)
    assert out["schema_version"] == "m8r_ai_conversation_resolution.v1"
    assert out["reresolution_performed"] is True
    assert out["raw_payload_retained"] is False
    assert out["resolved_contracts"][0]["expiry"] == "202607W4"


def test_cli_artifact_root_guard():
    assert safe_root("research/m8r/live_validation/x") == "research/m8r/live_validation/x"
    for bad in ["/tmp/x", "../x", "frontend/public/x", "research/generated/x"]:
        try:
            safe_root(bad)
        except SystemExit:
            pass
        else:
            raise AssertionError(bad)


def test_unavailable_exact_fixture_creates_no_ai_package(tmp_path):
    root = f"research/m8r/live_validation/unit-exact-unavailable-{tmp_path.name}"
    shutil.rmtree(root, ignore_errors=True)
    provider = FixtureUniverseProvider([{"contracts": []}, {"contracts": []}])
    out = run("TXO 209912 99999 C monthly", root, resolver=provider)
    assert out["status"] == "blocked"
    assert out["resolution"]["resolution_status"] == "exact_contract_unavailable"
    assert out["ai_package_id"] is None
    assert not list(Path(root).glob("*/ai_market_context_v1.json"))
    shutil.rmtree(root, ignore_errors=True)
