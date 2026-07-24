from __future__ import annotations

from pathlib import Path

import pytest

from scripts.m8r_05b_03.containment import validate_contained_relative_paths, validate_governed_output_root
from scripts.m8r_05b_03.errors import OrchestrationError


def test_output_traversal_and_absolute_paths_are_rejected(tmp_path):
    with pytest.raises(OrchestrationError, match="path_traversal_forbidden"):
        validate_contained_relative_paths(tmp_path, ["../escape.json"])
    with pytest.raises(OrchestrationError, match="absolute_output_path_forbidden|rooted_output_path_forbidden"):
        validate_contained_relative_paths(tmp_path, [str(Path(tmp_path, "x.json"))])


def test_output_outside_governed_root_and_frontend_public_are_rejected(tmp_path):
    with pytest.raises(OrchestrationError, match="output_root_not_absolute"):
        validate_governed_output_root("relative/root")
    forbidden = tmp_path / "frontend" / "public"
    forbidden.mkdir(parents=True)
    with pytest.raises(OrchestrationError, match="governed_output_root_forbidden"):
        validate_governed_output_root(forbidden)


def test_collision_rejected_without_filesystem_mutation(tmp_path):
    existing = tmp_path / "operations"
    existing.mkdir()
    (existing / "umeop-op-v1-37e7ffc42102745298c7.execution-request.json").write_text("existing")
    before = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    with pytest.raises(OrchestrationError, match="contained_output_path_collision"):
        validate_contained_relative_paths(tmp_path, ["operations/umeop-op-v1-37e7ffc42102745298c7.execution-request.json"])
    after = sorted(path.relative_to(tmp_path).as_posix() for path in tmp_path.rglob("*"))
    assert after == before
