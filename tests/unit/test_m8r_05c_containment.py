import pytest
import json
from pathlib import Path
import tempfile
import os

from scripts.m8r_05c.containment import materialize_outputs, validate_output_paths_only, _validate_relative_output_path
from scripts.m8r_05c.errors import ProjectionError

def test_relative_output_path_validation():
    assert _validate_relative_output_path("a/b/c.json") == ["a", "b", "c.json"]
    
    with pytest.raises(ProjectionError, match="output_path_absolute_unix_absolute"):
        _validate_relative_output_path("/a/b/c")
        
    with pytest.raises(ProjectionError, match="output_path_absolute_drive_rooted"):
        _validate_relative_output_path("C:/a/b/c")
        
    with pytest.raises(ProjectionError, match="output_path_traversal"):
        _validate_relative_output_path("a/../b.json")
        
    with pytest.raises(ProjectionError, match="output_path_hidden_file"):
        _validate_relative_output_path("a/.env")

def test_materialize_outputs_success():
    with tempfile.TemporaryDirectory() as d:
        result = {"schema_version": "unified_market_evidence_result.v1"}
        audit = {"schema_version": "unified_market_evidence_audit_package.v1"}
        md = "# Result"
        
        promoted = materialize_outputs(
            output_root=d,
            result_json=result,
            audit_package_json=audit,
            result_markdown=md,
            result_relative_path="ai_context/result.json",
            audit_relative_path="audit/audit.json",
            result_md_relative_path="ai_context/result.md"
        )
        
        assert "ai_context/result.json" in promoted
        assert "audit/audit.json" in promoted
        assert "ai_context/result.md" in promoted
        
        res_file = Path(d) / "ai_context" / "result.json"
        assert res_file.exists()
        assert json.loads(res_file.read_text(encoding="utf-8")) == result

def test_materialize_outputs_size_limit():
    with tempfile.TemporaryDirectory() as d:
        result = {"data": "x" * (60 * 1024 * 1024)}  # 60MB, exceeds 50MB
        audit = {"data": "test"}
        md = "# Result"
        
        with pytest.raises(ProjectionError, match="staged_file_too_large"):
            materialize_outputs(
                output_root=d,
                result_json=result,
                audit_package_json=audit,
                result_markdown=md,
                result_relative_path="ai_context/result.json",
                audit_relative_path="audit/audit.json",
                result_md_relative_path="ai_context/result.md"
            )
            
        assert not (Path(d) / "ai_context" / "result.json").exists()

def test_validate_output_paths_only():
    with tempfile.TemporaryDirectory() as d:
        validate_output_paths_only(
            output_root=d,
            result_relative_path="ai_context/result.json",
            audit_relative_path="audit/audit.json",
            result_md_relative_path="ai_context/result.md"
        )
        # Should not raise any errors, and no files should be created
        assert not (Path(d) / "ai_context").exists()
        assert not (Path(d) / "audit").exists()

def test_materialize_collision():
    with tempfile.TemporaryDirectory() as d:
        target = Path(d) / "ai_context" / "result.json"
        target.parent.mkdir(parents=True)
        target.touch()
        
        with pytest.raises(ProjectionError, match="output_path_already_exists"):
            materialize_outputs(
                output_root=d,
                result_json={},
                audit_package_json={},
                result_markdown="",
                result_relative_path="ai_context/result.json",
                audit_relative_path="audit/audit.json",
                result_md_relative_path="ai_context/result.md"
            )
