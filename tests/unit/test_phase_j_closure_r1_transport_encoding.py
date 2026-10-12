import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/fixtures/phase_j/closure_r1/source_rows.json"
EXPECTED_SHA256 = "3eafcfd3b70c213cdebc67500093a1880ba9914f07d84fa41163d40c04819cb6"


def test_j1_fixture_bytes_are_unchanged_utf8():
    raw = FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED_SHA256
    text = raw.decode("utf-8")
    assert any(ord(char) > 127 for char in text)
    assert {"mis", "twse", "tpex"}.issubset(json.loads(text))


def test_transport_installs_under_non_utf8_windows_default_without_invoking_source(tmp_path):
    counter = tmp_path / "source-invocations"
    code = r'''import json, locale, os, urllib.request
from pathlib import Path
from tests.helpers.phase_j_closure_r1_transport import install, load_source_rows_fixture
assert locale.getpreferredencoding(False).casefold() not in {"utf-8", "utf8"}
fixture = Path("tests/fixtures/phase_j/closure_r1/source_rows.json")
try:
    fixture.read_text()
except UnicodeDecodeError:
    pass
else:
    raise AssertionError("implicit-default-read-did-not-reproduce")
rows = load_source_rows_fixture()
assert {"mis", "twse", "tpex"}.issubset(rows)
original_urlopen = urllib.request.urlopen
install()
assert urllib.request.urlopen is not original_urlopen
counter = Path(os.environ["M8R_06_03_TEST_INVOCATION_COUNTER"])
assert not counter.exists() or not list(counter.iterdir())
print(json.dumps({"preferred_encoding": locale.getpreferredencoding(False), "fixture_loaded": True, "transport_installed": True, "source_invocations": 0}))'''
    env = os.environ.copy()
    env.update(
        PYTHONUTF8="0",
        M8R_06_03_EXECUTION_ENVIRONMENT="test",
        M8R_06_03_TEST_SOURCE_TRANSPORT="deterministic",
        M8R_06_03_TEST_INVOCATION_COUNTER=str(counter),
        PHASE_J_CLOSURE_R1_SCENARIO="J1-21",
    )
    completed = subprocess.run(
        [sys.executable, "-X", "utf8=0", "-c", code],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=True,
    )
    result = json.loads(completed.stdout)
    assert result["preferred_encoding"].casefold() not in {"utf-8", "utf8"}
    assert result["fixture_loaded"] is True
    assert result["transport_installed"] is True
    assert result["source_invocations"] == 0
    assert not counter.exists() or not list(counter.iterdir())
