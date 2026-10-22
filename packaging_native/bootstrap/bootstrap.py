"""Offline per-bundle bootstrap. Never initializes installation state."""
from __future__ import annotations
import argparse
import json
import os
import platform
from pathlib import Path
import re
import struct
import subprocess
import sys
try:
    from .package_integrity import verify_bundle
except ImportError:
    from package_integrity import verify_bundle

MARKER = 'runtime-marker.json'

def _env():
    env = {k:v for k,v in os.environ.items() if not k.upper().startswith(('PIP_', 'PYTHON'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', PIP_CONFIG_FILE=os.devnull)
    return env

def bootstrap(bundle):
    report = verify_bundle(bundle)
    root = Path(report['bundle_root'])
    if (os.name != 'nt' or platform.python_implementation() != 'CPython'
        or sys.version_info[:2] != (3,13) or struct.calcsize('P') != 8
        or platform.machine().lower() not in {'amd64','x86_64'}):
        raise RuntimeError('Windows CPython 3.13 x64 required')
    req = root / 'bootstrap/requirements-wheelhouse.txt'
    wheelhouse = root / 'wheelhouse'
    dep_manifest = root / 'dependency-manifest.json'
    if not req.is_file() or not wheelhouse.is_dir() or not dep_manifest.is_file():
        raise RuntimeError('bootstrap dependency resources missing')
    data = json.loads(dep_manifest.read_text(encoding='utf-8'))
    if not isinstance(data,dict) or data.get('schema_version') != 1 or not isinstance(data.get('dependencies'),list):
        raise RuntimeError('invalid dependency manifest')
    expected_deps = {}
    for dep in data['dependencies']:
        if not isinstance(dep,dict) or not isinstance(dep.get('name'),str) or not isinstance(dep.get('version'),str):
            raise RuntimeError('invalid dependency record')
        name = re.sub(r'[-_.]+','-',dep['name']).lower()
        if not name or not dep['version'] or name in expected_deps or name == 'pip':
            raise RuntimeError('invalid or duplicate dependency')
        expected_deps[name] = dep['version']
    if not expected_deps:
        raise RuntimeError('empty dependency manifest')
    runtime = root / 'runtime'
    marker = runtime / MARKER
    venv_dir = runtime / 'venv'
    expected_marker = {'bundle_root':str(root),'manifest_canonical_sha256':report['manifest_canonical_sha256']}
    existing = marker.exists()
    if existing and json.loads(marker.read_text(encoding='utf-8')) != expected_marker:
        raise RuntimeError('stale or relocated runtime; remove entire derived runtime directory and bootstrap again')
    if venv_dir.exists() and not existing:
        raise RuntimeError('unverified existing venv; remove entire derived runtime directory and bootstrap again')
    if existing and not venv_dir.is_dir():
        raise RuntimeError('runtime incomplete; remove entire derived runtime directory and bootstrap again')
    py = venv_dir / 'Scripts/python.exe'
    env = _env()
    if not existing:
        runtime.mkdir(exist_ok=True)
        subprocess.run([sys.executable,'-I','-B','-m','venv',str(venv_dir)],check=True,env=env)
        subprocess.run([str(py),'-I','-B','-m','pip','--isolated','install','--no-cache-dir',
                        '--disable-pip-version-check','--no-compile','--no-index','--find-links',str(wheelhouse),
                        '--only-binary=:all:','--require-hashes','-r',str(req)],check=True,env=env)
    subprocess.run([str(py),'-I','-B','-m','pip','--isolated','check','--disable-pip-version-check'],check=True,env=env)
    probe = "import importlib.metadata as m,json,re; print(json.dumps({re.sub(r'[-_.]+','-',d.metadata['Name'].lower()):d.version for d in m.distributions() if d.metadata.get('Name')}))"
    installed = json.loads(subprocess.check_output([str(py),'-I','-B','-c',probe],env=env,text=True))
    installed.pop('pip',None)
    if installed != expected_deps:
        raise RuntimeError('installed distributions differ from exact dependency manifest')
    if not existing:
        marker.write_text(json.dumps(expected_marker,sort_keys=True),encoding='utf-8')
    return {'status':'verified-existing' if existing else 'bootstrapped',**expected_marker,'python':str(py),'dependency_count':len(installed)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--bundle',type=Path,default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        print(json.dumps(bootstrap(args.bundle),sort_keys=True))
        return 0
    except (ValueError,RuntimeError,OSError,subprocess.CalledProcessError) as exc:
        print(str(exc),file=sys.stderr)
        return 1
if __name__ == '__main__':
    raise SystemExit(main())
