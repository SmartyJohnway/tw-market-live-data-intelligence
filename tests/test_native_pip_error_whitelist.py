"""Offline negative tests for hosted pip failure classification."""
from __future__ import annotations
import json
import pytest
from scripts.native_pip_error_whitelist import classify, classify_stderr_context

@pytest.mark.parametrize("message,expected", [
    ("ERROR: Could not install packages due to an OSError: [WinError 206] filename or extension is too long: SECRET", "PATH_TOO_LONG"),
    ("ERROR: [WinError 32] file is being used by another process: SECRET", "FILE_IN_USE"),
    ("ERROR: [WinError 5] Access is denied: SECRET", "ACCESS_DENIED"),
    ("ERROR: [Errno 2] No such file or directory: SECRET", "MISSING_PATH"),
    ("ERROR: Fatal error in launcher: Unable to create process: SECRET", "SCRIPT_LAUNCHER"),
    ("ERROR: UnicodeEncodeError: 'charmap' codec can't encode character SECRET", "UNICODE_CODEC"),
    ("ERROR: THESE PACKAGES DO NOT MATCH THE HASHES FROM THE REQUIREMENTS FILE: SECRET", "HASH_MISMATCH"),
    ("ERROR: No matching distribution found for SECRET", "WHEEL_MISSING"),
    ("ERROR: Failed while writing the installation record of SECRET", "INSTALL_RECORD"),
    ("ERROR: ResolutionImpossible due to conflicting dependencies SECRET", "RESOLUTION"),
    ("ERROR: Connection timed out: SECRET", "NETWORK"),
    ("ERROR: An exception within pip._internal: SECRET", "PIP_INTERNAL"),
])
def test_closed_categories(message, expected):
    output = classify(message)
    assert output["categories"] == [expected]
    assert output["count"] == 1
    assert "SECRET" not in json.dumps(output)

def test_unknown_fails_closed():
    out = classify("ERROR: unforeseen failure for C:\\private\\TOKEN_ABC")
    assert out["categories"] == []
    assert out["unclassified"] == 1
    assert "TOKEN_ABC" not in json.dumps(out)

def test_ignores_non_error_text():
    assert classify("ERROR: missing file" + "\n" + "DEBUG: unrelated text")["count"] == 1
    assert classify("The command 'ERROR: Fake' should not count")["count"] == 0

def test_multiple_error_lines_and_winerror_allowlist():
    raw = ("ERROR: [WinError 32] another process has file SECRET\n"
           "ERROR: [WinError 206] long path SECRET\n"
           "ERROR: [WinError 999] undisclosed classification SECRET\n")
    out = classify(raw)
    assert out["winerror_codes"] == ["32", "206"]
    assert out["unclassified"] == 1
    assert len(out["categories"]) == 2
    assert "SECRET" not in json.dumps(out)

def test_context_only_boolean_fields():
    out = classify_stderr_context("Installing collected packages\n"
        "ERROR: Could not install packages due to an OSError: SECRET")
    assert out["install_started_seen"]
    assert out["install_error_seen"]
    assert out["oserror_seen"]
    assert not out["install_completed_seen"]
    assert "SECRET" not in json.dumps(out)
