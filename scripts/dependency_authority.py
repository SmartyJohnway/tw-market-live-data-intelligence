"""Exact per-consumer dependency replay and deterministic SBOM authority.

Acquisition is explicit setup. Replay uses all hashed artifacts with no index,
no transitive resolution, followed by pip check. No product startup uses this.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if not __debug__:
    raise RuntimeError('Dependency verification requires assertions enabled')


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def load_consumer(name, root=ROOT):
    policy = json.loads((root / "config/dependency_authority.json").read_bytes())
    consumer = policy["consumers"][name]
    lock = json.loads((root / consumer["lock"]).read_bytes())
    rows = lock.get("wheels", lock.get("artifacts"))
    assert rows and len({r["wheel_filename"] for r in rows}) == len(rows)
    assert len({r.get("name", r.get("project")).lower().replace("_", "-") for r in rows}) == len(rows)
    for row in rows:
        assert Path(row["wheel_filename"]).name == row["wheel_filename"]
        assert row["wheel_filename"].endswith(".whl")
        assert len(row["sha256"]) == 64 and all(c in "0123456789abcdef" for c in row["sha256"])
        assert row.get("yanked") is False
        assert row["release_metadata_url"].startswith("https://pypi.org/pypi/")
    mcp = [r for r in rows if r.get("name", r.get("project")) == "mcp"]
    assert len(mcp) == 1 and mcp[0]["version"] == "1.29.0"
    return consumer, rows


def requirements(rows):
    return "".join(f"{r.get('name', r.get('project'))}=={r['version']} --hash=sha256:{r['sha256']}\n"
                   for r in sorted(rows, key=lambda r: r['wheel_filename']))


def verify_artifacts(rows, directory):
    expected = {r["wheel_filename"] for r in rows}
    assert {p.name for p in directory.iterdir()} == expected, "artifact closure differs"
    for row in rows:
        p = directory / row["wheel_filename"]
        assert p.is_file() and not p.is_symlink()
        assert hashlib.sha256(p.read_bytes()).hexdigest() == row["sha256"], "artifact bytes differ"


def sbom(root=ROOT):
    policy = json.loads((root / "config/dependency_authority.json").read_bytes())
    components = []
    for name in sorted(policy["consumers"]):
        consumer, rows = load_consumer(name, root)
        for r in sorted(rows, key=lambda r: r["wheel_filename"]):
            components.append({"consumer": name, "name": r.get("name", r.get("project")),
                "version": r["version"], "artifact": r["wheel_filename"], "sha256": r["sha256"],
                "source": r["release_metadata_url"], "python": consumer["python"],
                "platform": consumer["platform"], "lock": consumer["lock"]})
    browser=json.loads((root/'config/browser_artifact_authority.json').read_bytes())
    for row in browser['artifacts']:
        components.append({'consumer':'browser-linux','name':row['name'],'version':row['revision'],
            'artifact':row['filename'],'sha256':row['sha256'],'source':row['url'],
            'platform':browser['platform'],'lock':'config/browser_artifact_authority.json'})
    return {"format": "TW-Market deterministic first-party dependency SBOM", "schema_version": 1,
            "scope": "A3 validation dependency inputs; not final stable release", "components": components}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--consumer")
    p.add_argument("--wheelhouse", type=Path)
    p.add_argument("--work", type=Path)
    p.add_argument("--install", action="store_true")
    p.add_argument("--acquire", action="store_true", help="Explicit official setup acquisition")
    p.add_argument("--sbom", type=Path)
    a = p.parse_args()
    if a.sbom:
        a.sbom.write_bytes(canonical(sbom()))
        return
    consumer, rows = load_consumer(a.consumer)
    assert a.wheelhouse is not None
    if a.acquire:
        # Same exact official acquisition path accepted in A2, never a resolver.
        sys.path.insert(0, str(ROOT))
        from scripts.run_l7_a2_release_validation import acquire_wheels
        result = acquire_wheels({"artifacts": rows}, a.wheelhouse, download=True)
        assert a.work is not None
        a.work.mkdir(parents=True, exist_ok=True)
        (a.work / "setup-network.json").write_bytes(canonical(result))
    verify_artifacts(rows, a.wheelhouse)
    if a.install:
        assert sys.prefix != sys.base_prefix, "disposable venv required"
        assert f"{sys.version_info.major}.{sys.version_info.minor}" == consumer["python"]
        assert (sys.platform == "win32") == (consumer["platform"] == "win_amd64")
        assert a.work is not None
        if os.name == 'nt':
            assert a.work.resolve().is_relative_to(Path(r'C:\twmarket_temp\l7-a3'))
        a.work.mkdir(parents=True, exist_ok=True)
        req = a.work / "requirements-hashed.txt"
        req.write_bytes(requirements(rows).encode())
        subprocess.run([sys.executable, "-B", "-m", "pip", "install", "--disable-pip-version-check",
            "--no-index", "--no-cache-dir", "--no-compile", "--no-deps", "--only-binary=:all:",
            "--require-hashes", "--find-links", str(a.wheelhouse), "-r", str(req)], check=True)
        subprocess.run([sys.executable, "-B", "-m", "pip", "check"], check=True)
    print(json.dumps({"status": "PASS", "consumer": a.consumer, "artifacts": len(rows)}))


if __name__ == "__main__":
    main()
