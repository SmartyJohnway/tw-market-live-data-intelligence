"""Validate the network-free A5 L1-P0-R1 execution-instance lease contract."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A5_L1_P0_R1_EXECUTION_INSTANCE_LEASE_HARDENING_2026-10-09.json"
DOC = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A5_L1_P0_R1_EXECUTION_INSTANCE_LEASE_HARDENING_2026-10-09.md"
OLD_L1_RECORD = ROOT / "docs/governance/phase_j/PHASE_J_J_B04_A5_L1_P0_LIVE_RUNNER_HARDENING_2026-10-09.json"
LEASE_CLI = "--prepare-execution-lease --execution-environment cloud_clean_source_acceptance --execution-lease-file <EXTERNAL_PATH>"
LIVE_FLAGS = ["--live-acceptance", "--execution-environment", "--owner-authorization-json", "--execution-lease-file"]


def strict_json(path: Path) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise AssertionError(f"duplicate_json_key:{path}:{key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs)


def validate_contract(record: dict[str, Any]) -> dict[str, str]:
    assert record["gate"] == "J-B04-A5-L1-P0-R1"
    assert record["starting_head"] == "247e66f28424b205ddff1da3dd7cd07e0be9151c"
    assert record["starting_tree"] == "34cd17b7811db209c6e4d4c999864ef2a1f95442"
    assert record["main"] == "6daf6e2dcc6fd34e00e7e3831c25e98bb4d2399a"
    assert record["execution_instance_secret_required"] is True
    assert record["minimum_secret_bytes"] >= 32
    assert record["secret_persisted_in_repository"] is False
    assert record["secret_persisted_in_acceptance_runs"] is False
    assert record["authorization_binds_lease_hash"] is True
    assert record["consumed_receipt_binds_lease_hash"] is True
    assert record["lease_hash_format"] == "lowercase 64-character hexadecimal SHA-256"
    assert record["live_cli_required_flags"] == LIVE_FLAGS
    assert record["lease_preparation_cli"].startswith("--prepare-execution-lease")
    assert record["lease_external_path_required"] is True
    assert record["lease_refused_inside_repository"] is True
    assert record["live_mode_auto_regeneration"] is False
    assert record["owner_authorization_rewritten"] is False
    assert record["secret_exported_by_cli"] is False
    assert record["lease_preparation_is_owner_authorization"] is False
    assert record["production_execution_lease_prepared"] is False
    assert record["real_live_execution"] is False
    assert record["owner_live_authorization"] == "NOT PRESENT"
    assert record["network_calls"] == {"market_GET": 0, "market_HEAD": 0, "market_POST": 0,
        "security_master_live_acquisition": 0}
    assert record["canonical_state"] == {"H2_runtime": "INACTIVE", "selected_executor_id": None,
        "J-B04": "BLOCKING", "Phase J": "NOT_STARTED", "MCP": 6}
    return {"status": "PASS", "disposition": record["disposition"]}


def validate_repository() -> dict[str, Any]:
    record = strict_json(RECORD)
    old_l1 = strict_json(OLD_L1_RECORD)
    validate_contract(record)
    assert old_l1["authorization_contract"]["execution_lease_required"] is True
    assert "execution_instance_lease_sha256" in old_l1["authorization_contract"]["record_fields"]
    assert "execution_instance_lease_sha256" in old_l1["authority_consumption"]["receipt_fields"]
    assert old_l1["authority_consumption"]["receipt_fields"] == ["gate", "authorized_head_sha",
        "authorized_tree_sha", "statement_sha256", "execution_environment_class",
        "execution_instance_lease_sha256", "consumed_at_utc", "consumption_state"]

    from scripts.phase_j_b04_a5_bounded_live_acceptance import (
        EXECUTION_LEASE_MIN_BYTES, EXECUTION_ENVIRONMENTS, LEASE_SHA256_RE,
        expected_owner_statement, load_execution_lease, prepare_execution_lease,
        run_live_acceptance, SingleUseAuthority,
    )
    assert EXECUTION_LEASE_MIN_BYTES >= 32
    assert EXECUTION_ENVIRONMENTS == {"installation_bound", "cloud_clean_source_acceptance"}
    assert LEASE_SHA256_RE.fullmatch("a" * 64) and not LEASE_SHA256_RE.fullmatch("A" * 64)
    fake_hash = hashlib.sha256(b"x" * 32).hexdigest()
    statement = expected_owner_statement("a" * 40, fake_hash)
    assert f"WITH EXECUTION LEASE {fake_hash}:" in statement
    assert "AUTHORIZE J-B04-A5 LIVE ON HEAD aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa:\n" not in statement
    try:
        SingleUseAuthority({"gate": "J-B04-A5"}, head="a" * 40)
    except Exception:
        pass
    else:
        raise AssertionError("lease-free authorization accepted")

    source = (ROOT / "scripts/phase_j_b04_a5_bounded_live_acceptance.py").read_text(encoding="utf-8")
    live_source = __import__("inspect").getsource(run_live_acceptance)
    assert 'parser.add_argument("--prepare-execution-lease"' in source
    assert 'parser.add_argument("--execution-lease-file"' in source
    assert 'parser.add_argument("--owner-authorization-json"' in source
    assert "secrets.token_bytes(EXECUTION_LEASE_MIN_BYTES)" in source
    assert "O_EXCL" in source and "0o600" in source
    assert "J_B04_A5_EXECUTION_LEASE_MISSING" in source
    assert "J_B04_A5_EXECUTION_LEASE_INVALID" in source
    assert "J_B04_A5_EXECUTION_LEASE_HASH_MISMATCH" in source
    assert "load_execution_lease" in live_source
    assert live_source.index("load_execution_lease(Path(") < live_source.index("atomic_create_text_exclusive(str(")
    assert live_source.index("atomic_create_text_exclusive(str(") < live_source.index("authority.consume()")
    assert live_source.index("authority.consume()") < live_source.index("transport(timeout_seconds=TIMEOUT)")
    assert '"execution_instance_lease_sha256"' in live_source

    tests = (ROOT / "tests/unit/test_phase_j_b04_a5_l1_runner.py").read_text(encoding="utf-8")
    required = ("test_lease_preparation_creates_random_external_secret",
        "test_lease_prepare_never_overwrites_existing_secret", "test_lease_paths_inside_repository_and_symlink",
        "test_missing_wrong_and_truncated_lease", "test_cloud_workspace_loss_replay_requires_original_lease",
        "test_cloud_workspace_loss_with_new_unrelated_lease", "test_fake_transport_failure_receipt",
        "test_old_lease_free_owner_statement")
    assert all(name in tests for name in required)

    markdown = DOC.read_text(encoding="utf-8")
    markdown_flat = " ".join(markdown.split())
    for flag in ("--prepare-execution-lease", "--execution-environment cloud_clean_source_acceptance",
                 "--execution-lease-file <EXTERNAL_PATH>"):
        assert flag in markdown
    assert "WITH EXECUTION LEASE <EXECUTION_INSTANCE_LEASE_SHA256>:" in markdown
    assert "not a remote transactional lock" in markdown_flat
    assert "workspace-loss replay resistance" in markdown_flat
    forbidden_secret_names = ("execution_instance_lease_secret", "TEST_SECRET")
    serialized = RECORD.read_text(encoding="utf-8") + markdown
    assert not any(name in serialized for name in forbidden_secret_names)

    from scripts.validate_phase_j_b04_a5_bounded_live_acceptance import validate_repository as validate_p0
    from scripts.validate_phase_j_b04_a5_l1_p0_live_runner import validate_repository as validate_l1
    validate_p0()
    validate_l1()
    assert subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=ROOT, text=True).strip() == record["main"]
    runs = ROOT / "docs/governance/phase_j/acceptance_runs"
    assert not any(runs.rglob("owner_authorization_consumed.json")) if runs.exists() else True
    return {"status": "PASS", "disposition": record["disposition"], "P0_validator": "PASS",
        "L1_P0_validator": "PASS", "market_GET_HEAD_POST": "0/0/0", "security_master_live_calls": 0,
        "MCP": 6}


if __name__ == "__main__":
    print(json.dumps(validate_repository(), indent=2, sort_keys=True))
