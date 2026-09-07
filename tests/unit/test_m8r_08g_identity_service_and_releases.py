from __future__ import annotations
import json
from pathlib import Path
import pytest
from scripts.m8r_08g_security_master_releases import (
    LocalSecurityMasterError,
    activate_qualified_release,
    build_candidate_release,
    load_qualified_release,
    qualify_candidate_release,
    load_active_identity_service,
    list_releases,
    retire_qualified_release,
)


def rec(code="2330", isin="TW0002330008", typ="common_share"):
    return {
        "canonical_target_id": f"TWSE:{code}",
        "identity": {"security_code": code, "isin": isin},
        "classification": {"market": "TWSE", "instrument_type": typ},
        "lifecycle": {
            "state": "listed",
            "resolution_status": "resolved",
            "basis_event_ids": [],
            "events": [],
        },
        "execution_eligibility": {"status": "allowed", "reason_codes": []},
    }


def prov():
    return {
        "source_type": "test",
        "snapshot_id": "test",
        "source_content_hashes": {"fixture": "a" * 64},
        "producer_skill": {
            "name": "test",
            "skill_version": "1",
            "skill_contract_hash": "b" * 64,
        },
    }


def qualify(root, rid, records):
    build_candidate_release(
        root=root, release_id=rid, records=records, source_provenance=prov()
    )
    return qualify_candidate_release(root=root, release_id=rid)


def test_constructor_cannot_declare_qualified(tmp_path):
    from scripts.m8r_08g_security_master_releases import build_qualified_release

    with pytest.raises(
        LocalSecurityMasterError, match="qualification_constructor_prohibited"
    ):
        build_qualified_release()


def test_candidate_passes_then_activates(tmp_path):
    rid = "security-master-20260907T000000Z"
    d, r = qualify(tmp_path, rid, [rec()])
    assert d and r["status"] == "PASS"
    assert (
        activate_qualified_release(root=tmp_path, release_id=rid)["release_id"] == rid
    )


def test_invalid_isin_rejected_and_active_unchanged(tmp_path):
    good = "security-master-20260907T000000Z"
    qualify(tmp_path, good, [rec()])
    activate_qualified_release(root=tmp_path, release_id=good)
    bad = "security-master-20260907T000001Z"
    d, x = qualify(tmp_path, bad, [rec(isin="bad")])
    assert (
        d is None
        and json.loads((x / "qualification.json").read_text())["status"] == "FAIL"
    )
    assert json.loads((tmp_path / "active.json").read_text())["release_id"] == good


def test_mismatch_and_duplicates_rejected(tmp_path):
    a = rec()
    a["instrument_id"] = "TW0002330016"
    assert qualify(tmp_path, "security-master-20260907T000000Z", [a])[0] is None
    b = rec(code="2331")
    b["identity"]["isin"] = "TW0002330008"
    assert qualify(tmp_path, "security-master-20260907T000001Z", [rec(), b])[0] is None
    assert (
        qualify(tmp_path, "security-master-20260907T000002Z", [rec(), rec()])[0] is None
    )


def test_schema_invalid_candidate_and_pointer_rejected(tmp_path):
    rid = "security-master-20260907T000000Z"
    build_candidate_release(
        root=tmp_path, release_id=rid, records=[rec()], source_provenance=prov()
    )
    p = tmp_path / "candidates" / rid / "index.json"
    x = json.loads(p.read_text())
    x["record_count"] = "bad"
    p.write_text(json.dumps(x))
    assert qualify_candidate_release(root=tmp_path, release_id=rid)[0] is None
    (tmp_path / "active.json").write_text("{}")
    with pytest.raises(LocalSecurityMasterError, match="active_pointer_schema_invalid"):
        load_active_identity_service(root=tmp_path)


def test_structurally_incomplete_record_is_rejected(tmp_path):
    incomplete = rec()
    incomplete.pop("lifecycle")

    qualified, rejected = qualify(
        tmp_path,
        "security-master-20260907T000000Z",
        [incomplete],
    )

    assert qualified is None
    assert (
        "record_schema_invalid"
        in json.loads((rejected / "qualification.json").read_text())["reason_codes"]
    )


def test_release_hash_and_lifecycle_status_schema_mismatches_fail_closed(tmp_path):
    release_id = "security-master-20260907T000000Z"
    qualified, _ = qualify(tmp_path, release_id, [rec()])
    assert qualified is not None

    release_path = qualified / "release.json"
    release = json.loads(release_path.read_text())
    release["manifest_sha256"] = "0" * 64
    release_path.write_text(json.dumps(release))
    with pytest.raises(
        LocalSecurityMasterError, match="release_manifest_hash_mismatch"
    ):
        load_qualified_release(root=tmp_path, release_id=release_id)

    rejected_id = "security-master-20260907T000001Z"
    qualify(tmp_path, rejected_id, [rec(isin="bad")])
    rejected_status = tmp_path / "rejected" / rejected_id / "release.json"
    rejected_status.write_text("{}")
    with pytest.raises(
        LocalSecurityMasterError, match="rejected_status_schema_invalid"
    ):
        list_releases(root=tmp_path)


def test_listing_history_not_fabricated_and_history_contains_governed_states(tmp_path):
    r = rec()
    r["listing_history"] = []
    a = "security-master-20260907T000000Z"
    b = "security-master-20260907T000001Z"
    d, _ = qualify(tmp_path, a, [r])
    assert (
        json.loads((d / "index.json").read_text())["records"][0]["listing_history"]
        == []
    )
    qualify(tmp_path, b, [rec(code="2331", isin="TW0002331006")])
    activate_qualified_release(root=tmp_path, release_id=a)
    retire_qualified_release(root=tmp_path, release_id=b, reason="test")
    qualify(tmp_path, "security-master-20260907T000002Z", [rec(isin="bad")])
    assert {"ACTIVE", "RETIRED", "REJECTED"} <= {
        x["state"] for x in list_releases(root=tmp_path)
    }


def test_not_initialized_has_no_fallback(tmp_path):
    with pytest.raises(LocalSecurityMasterError, match="NOT_INITIALIZED"):
        load_active_identity_service(root=tmp_path)


def test_records_import_is_non_production(tmp_path):
    from scripts import manage_security_master as manage
    from scripts import m8r_08g_security_master_releases as releases

    source = tmp_path / "records.json"
    source.write_text(json.dumps({"records": [rec()]}))
    assert (
        manage.main(
            ["update", "--root", str(tmp_path / "local"), "--records", str(source)]
        )
        == 1
    )
    assert not (tmp_path / "local" / "active.json").exists()


def test_live_failure_leaves_active_unchanged(tmp_path, monkeypatch):
    from scripts import manage_security_master as manage

    old = "security-master-20260907T000000Z"
    qualify(tmp_path, old, [rec()])
    activate_qualified_release(root=tmp_path, release_id=old)

    class Failed:
        returncode = 1

    monkeypatch.setattr(manage.subprocess, "run", lambda *a, **k: Failed())
    assert manage.main(["update", "--root", str(tmp_path), "--live"]) == 1
    assert json.loads((tmp_path / "active.json").read_text())["release_id"] == old


def test_live_success_qualifies_and_activates_in_one_command(tmp_path, monkeypatch):
    from scripts import manage_security_master as manage
    from scripts import m8r_08g_security_master_releases as releases

    bundle = (
        tmp_path
        / "data"
        / "security_master"
        / "input_bundles"
        / "m8r06-01b-20990101T000000Z"
    )
    bundle.mkdir(parents=True)
    (bundle / "dryrun_snapshot.json").write_text(
        json.dumps(
            {
                "snapshot_id": "s",
                "records": [rec()],
                "source_skill": {
                    "name": "test",
                    "skill_version": "1",
                    "skill_contract_hash": "b" * 64,
                },
            }
        )
    )

    class Success:
        returncode = 0

    monkeypatch.setattr(manage, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(releases, "_commit", lambda: "c" * 40)
    monkeypatch.setattr(manage.subprocess, "run", lambda *a, **k: Success())
    assert (
        manage.main(
            [
                "update",
                "--root",
                str(tmp_path / "local"),
                "--live",
                "security-master-20990101T000000Z",
            ]
        )
        == 0
    )
    assert (
        json.loads((tmp_path / "local" / "active.json").read_text())["release_id"]
        == "security-master-20990101T000000Z"
    )
