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


def test_mis_diagnostic_is_normalized_and_contains_stage_reason(tmp_path):
    root = f"research/m8r/live_validation/unit-diagnostic-{tmp_path.name}"
    shutil.rmtree(root, ignore_errors=True)
    universe = {"contracts": [{"instrument_type":"option","product":"TXO","expiry":"202607W4","contract_type":"weekly","session":"regular","strike":"44900","call_put":"C"},{"instrument_type":"option","product":"TXO","expiry":"202607W4","contract_type":"weekly","session":"regular","strike":"44900","call_put":"P"}]}
    provider = FixtureUniverseProvider([universe, universe], reference_value=None)
    out = run("現在台指選擇權怎麼樣？", root, resolver=provider)
    diag_path = Path(root) / "mis_conversational_resolution_diagnostic.json"
    assert out["status"] == "blocked"
    assert diag_path.exists()
    text = diag_path.read_text(encoding="utf-8")
    assert "raw_rows" not in text and "SockJS" not in text and "cookie" not in text.lower()
    diag = __import__("json").loads(text)
    assert diag["failure_layer"] == "current_reference_unavailable"
    assert diag["raw_payload_retained"] is False
    assert diag["full_option_chain_retained"] is False
    shutil.rmtree(root, ignore_errors=True)
