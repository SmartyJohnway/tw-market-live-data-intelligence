import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]


def test_closure_r2_json_reader_handles_utf8_under_cp950(tmp_path):
    path = tmp_path / "source-artifact.json"
    path.write_bytes('{"caveat":"來源證據"}'.encode("utf-8"))
    code = r'''import json, locale, sys
from pathlib import Path
from tests.helpers.phase_j_closure_r2 import read_json_utf8
assert locale.getpreferredencoding(False).casefold() not in {"utf-8", "utf8"}
value = read_json_utf8(sys.argv[1])
assert value["caveat"] == "來源證據"
print(json.dumps({"preferred_encoding": locale.getpreferredencoding(False), "utf8_json_read": True}))'''
    env = os.environ.copy()
    env["PYTHONUTF8"] = "0"
    completed = subprocess.run(
        [sys.executable, "-X", "utf8=0", "-c", code, str(path)],
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
    assert result["utf8_json_read"] is True
