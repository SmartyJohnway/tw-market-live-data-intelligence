from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts import test_governance_authority as roles
from scripts import validate_current_test_governance as current
from scripts import validate_test_governance_tg5 as tg5

ROOT = Path(__file__).resolve().parents[2]


def inputs():
    return (current.load(ROOT / "config/test_governance_authority.json"),
            current.load(ROOT / "config/test_execution_profiles.json"))


def test_current_roles_and_existing_consumers_resolve():
    authority, config = inputs()
    assert current.validate(authority, config)["status"] == "PASS"
    for role, profile in current.EXPECTED_ROLES.items():
        assert roles.profile_name_for_role(role) == profile
    assert roles.profile_name_for_role("current") == "default-ci"
    assert roles.profile_name_for_role("release") == "release-preflight-current"
    assert roles.profile_paths_for_role("broad_current") >= current.MANDATORY
    with pytest.raises(ValueError):
        roles.profile_name_for_role("unknown")


def test_legitimate_current_addition_does_not_change_historical_acceptance(tmp_path, monkeypatch):
    authority, config = inputs()
    # Valid existing current test, not currently in either explicit list.
    path = "tests/unit/test_phase_j_closure_authority_reconciliation.py"
    assert (ROOT / path).is_file()
    for name in ("default-ci", "full-current"):
        assert path not in config["profiles"][name]["pytest_paths"]
        config["profiles"][name]["pytest_paths"].append(path)
    assert current.validate(authority, config)["status"] == "PASS"
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in (tg5.TG4, tg5.TG5, tg5.ROLLBACK)}
    # Historical validator must not even read today's authority or profiles.
    monkeypatch.setattr(tg5, "PROFILES", tmp_path / "absent-profiles.json")
    monkeypatch.setattr(tg5, "AUTHORITY", tmp_path / "absent-authority.json")
    assert tg5.validate_static()["new_default_file_count"] == 93
    assert before == {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in before}


@pytest.mark.parametrize("name", ["default-ci", "full-current"])
@pytest.mark.parametrize("path", sorted(current.MANDATORY))
def test_mandatory_omission_fails(name, path):
    authority, config = inputs()
    config["profiles"][name]["pytest_paths"].remove(path)
    with pytest.raises(ValueError, match="mandatory current test omitted"):
        current.validate(authority, config)


@pytest.mark.parametrize("marker", ["network", "live", "browser", "performance", "release_preflight", "historical"])
def test_exclusion_weakening_fails(marker):
    authority, config = inputs()
    config["profiles"]["default-ci"]["pytest_expression"] = current.CURRENT_EXPRESSION.replace("not " + marker, marker)
    with pytest.raises(ValueError, match="exclusion policy weakened"):
        current.validate(authority, config)


def test_s1_selected_by_both_current_gates():
    import scripts.run_test_profile as runner
    for name in ("default-ci", "full-current"):
        command = runner.resolve_profile(name)[0]
        assert "tests/unit/test_current_v3_validation_authority.py" in command
        assert command[command.index("-m", 3) + 1] == current.CURRENT_EXPRESSION


@pytest.mark.parametrize("mutation,match", [
    ("missing_profile", "missing profile"), ("invalid_path", "invalid path"),
    ("duplicate_path", "duplicate path"), ("duplicate_role", "duplicated role"),
    ("release_only", "release-only enrollment"), ("historical_hash", "historical evidence changed"),
    ("count", "mixed historical/current"), ("release_delegate", "release delegation"),
    ("historical_path", "historical replay coverage"), ("rollback_path", "rollback diagnostic semantics"),
])
def test_fail_closed(mutation, match):
    authority, config = inputs()
    profile = config["profiles"]["default-ci"]
    if mutation == "missing_profile": del config["profiles"]["full-current"]
    elif mutation == "invalid_path": profile["pytest_paths"].append("tests/does_not_exist.py")
    elif mutation == "duplicate_path": profile["pytest_paths"].append(profile["pytest_paths"][0])
    elif mutation == "duplicate_role": authority["roles"]["historical"] = "default-ci"
    elif mutation == "release_only": profile["pytest_paths"].append(config["profiles"]["release-preflight-current"]["pytest_paths"][0])
    elif mutation == "historical_hash": next(iter(authority["historical_evidence"].values()))["sha256"] = "0" * 64
    elif mutation == "historical_path": config["profiles"]["historical-milestone-replay"]["pytest_paths"].pop()
    elif mutation == "rollback_path": config["profiles"]["pre-tg5-default-ci"]["pytest_paths"].pop()
    elif mutation == "count": authority["expected_selected_nodes"] = 778
    elif mutation == "release_delegate": config["profiles"]["release-blocking-ci"]["authoritative_runner"] = []
    with pytest.raises(ValueError, match=match):
        current.validate(authority, config)


@pytest.mark.parametrize("mutation", ["metadata", "trigger", "profile"])
def test_workflow_truth_drift_fails(tmp_path, mutation):
    authority, _ = inputs()
    for path in current.EXPECTED_WORKFLOWS:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((ROOT / path).read_text())
    if mutation == "metadata":
        authority["ci_workflows"][".github/workflows/ci.yml"]["trigger"] = "pull_request"
    else:
        target = tmp_path / ".github/workflows/ci.yml"
        text = target.read_text()
        text = text.replace("workflow_dispatch:", "pull_request:") if mutation == "trigger" else text.replace(
            "run_test_profile.py default-ci", "run_test_profile.py full-current")
        target.write_text(text)
    with pytest.raises(ValueError, match="workflow"):
        current.validate_workflows(authority, tmp_path)


@pytest.mark.parametrize("name", ["default-ci", "full-current"])
def test_r1_six_path_attack_rejected(name):
    authority, config = inputs()
    config["profiles"][name]["pytest_paths"] = sorted(current.MANDATORY)
    with pytest.raises(ValueError, match="coverage path floor lost|broad-current coverage lost"):
        current.validate(authority, config)


@pytest.mark.parametrize("name", ["default-ci", "full-current"])
def test_r1_nonmandatory_path_removal_rejected(name):
    authority, config = inputs()
    profile = config["profiles"][name]
    profile["pytest_paths"].remove(next(p for p in profile["pytest_paths"] if p not in current.MANDATORY))
    with pytest.raises(ValueError, match="coverage path floor lost|broad-current coverage lost"):
        current.validate(authority, config)


def test_r1_effective_selection_loss_rejected(monkeypatch):
    from scripts import run_current_merge_gate as gate
    authority, config = inputs()
    floor = current.load(ROOT / gate.FLOOR)
    nodes = floor["profiles"]["default-ci"]["selected_nodes"][1:]
    monkeypatch.setattr(gate, "observe", lambda *a, **kw: {"selected": nodes})
    with pytest.raises(ValueError, match="governed selection disappeared"):
        current.validate(authority, config)


def test_r1_real_marker_deselection_and_superset(tmp_path):
    from scripts import run_current_merge_gate as gate
    path = tmp_path / "test_selection.py"
    path.write_text("def test_original(): pass\n")
    profile = {"pytest_paths": [str(path)], "pytest_expression": "not historical"}
    original = gate.observe(profile, collect=True, quiet=True, root=tmp_path)["selected"]
    floor = {"profiles": {"example": {"selected_nodes": original}}}
    path.write_text("import pytest\n@pytest.mark.historical\ndef test_original(): pass\ndef test_added(): pass\n")
    selected = gate.observe(profile, collect=True, quiet=True, root=tmp_path)["selected"]
    with pytest.raises(ValueError, match="governed selection disappeared"):
        gate.check_selection(floor, "example", selected)
    path.write_text("def test_original(): pass\ndef test_added(): pass\n")
    selected = gate.observe(profile, collect=True, quiet=True, root=tmp_path)["selected"]
    gate.check_selection(floor, "example", selected)
    assert len(selected) > len(original)


def r1_observation():
    from scripts import run_current_merge_gate as gate
    floor = current.load(ROOT / gate.FLOOR)
    nodes = floor["profiles"]["default-ci"]["selected_nodes"]
    reports = {n: [{"when": "setup", "outcome": "passed", "wasxfail": False, "detail": ""},
                   {"when": "call", "outcome": "failed" if n in floor["known_diagnostics"] else "passed",
                    "wasxfail": False, "detail": ""},
                   {"when": "teardown", "outcome": "passed", "wasxfail": False, "detail": ""}] for n in nodes}
    return floor, {"selected": list(nodes), "reports": reports, "exitstatus": 1}


@pytest.mark.parametrize("mutation", ["known_only", "new_failure", "disappear", "now_pass", "skip", "xfail", "setup_failure", "collection_error"])
def test_r1_merge_result_model(mutation):
    from scripts import run_current_merge_gate as gate
    floor, observation = r1_observation()
    node = next(iter(floor["known_diagnostics"]))
    if mutation == "new_failure":
        other = next(n for n in observation["selected"] if n not in floor["known_diagnostics"])
        observation["reports"][other][1]["outcome"] = "failed"
    elif mutation == "disappear": observation["selected"].remove(node)
    elif mutation == "now_pass": observation["reports"][node][1]["outcome"] = "passed"
    elif mutation == "skip": observation["reports"][node][1]["outcome"] = "skipped"
    elif mutation == "xfail": observation["reports"][node][1].update(outcome="skipped", wasxfail=True)
    elif mutation == "setup_failure": observation["reports"][node][0]["outcome"] = "failed"
    elif mutation == "collection_error": observation["exitstatus"] = 2
    result = gate.classify(floor, observation)
    assert result["MERGE_VERDICT"] == ("PASS" if mutation in {"known_only", "now_pass"} else "FAIL")
    if mutation == "known_only":
        assert result["blocking_failures"] == 0 and result["known_diagnostic_failures"] == 12
    if mutation == "now_pass": assert result["known_diagnostic_now_passing"] == [node]


def test_r1_unknown_classification_and_raw_merge_role_rejected():
    authority, config = inputs()
    authority["roles"]["merge"] = "default-ci"
    with pytest.raises(ValueError, match="role"):
        current.validate(authority, config)
