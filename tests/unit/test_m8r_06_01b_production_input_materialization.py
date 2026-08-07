"""Tests for the M8R-06-01B production input materialization and SKILL_PATH fix."""
import json
import copy
from pathlib import Path

import pytest

from scripts.m8r_03d_f1_security_master_snapshot_exporter import (
    export_verified_security_master_snapshot,
    sha256_json,
    SKILL_PATH,
    ROOT,
)
from scripts.m8r_03d_f1_security_master_snapshot_adapter import (
    validate_verified_security_master_snapshot,
)

FIX = Path("tests/fixtures/m8r_03d_f1")


def load(n):
    return json.loads((FIX / n).read_text(encoding="utf-8"))


class TestSkillPathSerializationFix:
    """Regression tests for the SKILL_PATH Path→string fix."""

    def test_skill_path_is_path_object(self):
        """SKILL_PATH must be a Path object (confirming the type before fix)."""
        assert isinstance(SKILL_PATH, Path)

    def test_exported_snapshot_is_json_serializable(self):
        """The exported snapshot must be JSON-serializable (no Path objects)."""
        rec = load("classification_records.json")
        ev = load("lifecycle_events.json")
        ctx = load("source_context.json")
        snap, man = export_verified_security_master_snapshot(
            classification_records=rec,
            lifecycle_events=ev,
            source_context=ctx,
            generated_at_utc="2026-07-16T00:00:00Z",
            effective_observation_date="2026-07-16",
        )
        # This will raise TypeError if Path objects are embedded
        serialized = json.dumps(snap, ensure_ascii=False)
        assert '"skill_path"' in serialized

    def test_skill_path_matches_schema_const(self):
        """The skill_path in the snapshot must be the expected string constant."""
        rec = load("classification_records.json")
        ev = load("lifecycle_events.json")
        ctx = load("source_context.json")
        snap, _ = export_verified_security_master_snapshot(
            classification_records=rec,
            lifecycle_events=ev,
            source_context=ctx,
            generated_at_utc="2026-07-16T00:00:00Z",
            effective_observation_date="2026-07-16",
        )
        assert snap["source_skill"]["skill_path"] == "skills/tw-security-master-classifier"

    def test_exported_snapshot_validates_after_fix(self):
        """The full export+validate round-trip must pass after the fix."""
        rec = load("classification_records.json")
        ev = load("lifecycle_events.json")
        ctx = load("source_context.json")
        snap, man = export_verified_security_master_snapshot(
            classification_records=rec,
            lifecycle_events=ev,
            source_context=ctx,
            generated_at_utc="2026-07-16T00:00:00Z",
            effective_observation_date="2026-07-16",
        )
        result = validate_verified_security_master_snapshot(snap, man)
        assert result["valid"] is True


class TestQualificationTaxonomy:
    """Test that the qualification taxonomy covers all expected statuses."""

    def test_all_statuses_defined(self):
        """All qualification statuses must be correctly routed by qualify_record."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "m8r_06_01b",
            str(ROOT / "scripts" / "m8r_06_01b_materialize_production_inputs.py"),
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Test Dual Lane -> QUALIFIED_PRODUCTION_INPUT
        assert mod.qualify_record({
            "classification": {"classification_status": "confirmed_dual_lane"},
            "observation": {"status": "observed_in_capture"}
        }, {}) == mod.QUAL_PRODUCTION

        # Test Single Lane -> QUALIFIED_WITH_CAVEATS
        assert mod.qualify_record({
            "classification": {"classification_status": "confirmed_official_single_lane"},
            "observation": {"status": "observed_in_capture"}
        }, {}) == mod.QUAL_CAVEATS

        # Test Fixture -> REJECTED_FIXTURE_ONLY
        assert mod.qualify_record({
            "observation": {"status": "fixture_observation_only"}
        }, {}) == mod.QUAL_REJECTED_FIXTURE

        # Test Historical -> REJECTED_HISTORICAL_ONLY
        assert mod.qualify_record({
            "observation": {"status": "historical_capture"}
        }, {}) == mod.QUAL_REJECTED_HISTORICAL

        # Test Identity Conflict -> REJECTED_IDENTITY_CONFLICT
        assert mod.qualify_record({
            "conflicts": [{"severity": "hard", "category": "identity_conflict"}],
            "observation": {"status": "observed_in_capture"}
        }, {}) == mod.QUAL_REJECTED_IDENTITY

        # Test Quarantine -> QUARANTINED
        assert mod.qualify_record({
            "classification": {"classification_status": "quarantine_conflict"},
            "observation": {"status": "observed_in_capture"}
        }, {}) == mod.QUAL_QUARANTINED
