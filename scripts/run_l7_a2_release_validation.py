"""Pre-publication integration using the existing A1 and L6 authorities.

Python 3.13 uses the A3 per-consumer dependency authority. Setup downloads are
explicit and never occur in product acceptance; A2 historical evidence is frozen.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.release_validation_source import exact_release_validation_source


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8')


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def acquire_wheels(lock, destination, *, download=False):
    """Exact official artifacts only; no resolver or version substitution."""
    rows = lock.get('wheels', lock.get('artifacts'))
    if not isinstance(rows, list) or not rows:
        raise ValueError('missing exact artifact authority')
    destination.mkdir(parents=True, exist_ok=True)
    requests = []
    for row in rows:
        name = row['wheel_filename']
        if Path(name).name != name or not name.endswith('.whl'):
            raise ValueError('unsafe wheel identity')
        path = destination/name
        if not path.exists():
            if not download:
                raise ValueError(f'missing pinned setup artifact: {name}')
            metadata_url = row.get('release_metadata_url') or f"https://pypi.org/pypi/{row.get('project',row.get('name'))}/{row['version']}/json"
            if not metadata_url.startswith('https://pypi.org/pypi/'):
                raise ValueError('unapproved setup metadata authority')
            with urllib.request.urlopen(metadata_url, timeout=60) as response:
                metadata = json.load(response)
            requests.append({'phase':'setup', 'url':metadata_url})
            matches = [v for v in metadata['urls'] if v['filename']==name and v['digests']['sha256']==row['sha256'] and not v['yanked']]
            if len(matches)!=1 or not matches[0]['url'].startswith('https://files.pythonhosted.org/'):
                raise ValueError('official artifact identity mismatch')
            with urllib.request.urlopen(matches[0]['url'], timeout=120) as response:
                data=response.read()
            requests.append({'phase':'setup', 'url':matches[0]['url']})
            if hashlib.sha256(data).hexdigest()!=row['sha256']:
                raise ValueError('download hash mismatch')
            path.write_bytes(data)
        if sha(path)!=row['sha256']:
            raise ValueError(f'pinned setup artifact hash mismatch: {name}')
    if {p.name for p in destination.glob('*.whl')} != {r['wheel_filename'] for r in rows}:
        raise ValueError('unexpected setup wheel')
    return {'requests':requests, 'artifact_count':len(rows), 'all_sha256_verified':True}



def authorized_windows_workspace(work: Path) -> bool:
    return any(work.is_relative_to(Path(r'C:\twmarket_temp') / scope) for scope in ('l7-a2', 'l7-a3', 'l7-a4', 'l7-a6'))

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source-commit', required=True)
    ap.add_argument('--source-tree', required=True)
    ap.add_argument('--work', type=Path, required=True)
    ap.add_argument('--wheelhouse', type=Path, required=True)
    ap.add_argument('--download-setup', action='store_true')
    ap.add_argument('--provision', action='store_true', help='Explicit prerequisite installation into the current fresh validation venv')
    ap.add_argument('--native', action='store_true')
    ap.add_argument('--gate', action='store_true')
    args=ap.parse_args()
    if not (args.gate or args.native):
        ap.error('select at least one actual acceptance: --gate or --native')
    exact_release_validation_source(git,args.source_commit,args.source_tree)
    work=args.work.resolve()
    if os.name=='nt' and not authorized_windows_workspace(work):
        raise ValueError('output must remain under the authorized A2/A3/A4/A6 C workspace')
    if work.is_relative_to(ROOT) or work.exists():
        raise ValueError('choose a fresh output outside source checkout')
    work.mkdir(parents=True)
    save(work/'source.json',{'commit':args.source_commit,'tree':args.source_tree,'clean':True,'validation_only':True})
    lock=json.loads((ROOT/'packaging_native/wheelhouse-lock.json').read_text())
    save(work/'setup-network.json',acquire_wheels(lock,args.wheelhouse.resolve(),download=args.download_setup))
    def run(label, command):
        result=subprocess.run(command,cwd=ROOT,text=True,encoding='utf-8',errors='replace',capture_output=True)
        save(work/(label+'.json'),{'command':command,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        if result.returncode:
            raise RuntimeError(f'{label} failed; inspect {work/(label+".json")}')
        return result
    if args.provision:
        if sys.prefix==sys.base_prefix:
            raise ValueError('prerequisites may only be installed into a fresh validation venv')
        requirements=work/'setup-requirements.txt'
        requirements.write_text('\n'.join(f"{r['project']}=={r['version']} --hash=sha256:{r['sha256']}" for r in lock['wheels'])+'\n',encoding='utf-8')
        run('setup-install',[sys.executable,'-B','-m','pip','install','--no-index','--no-cache-dir','--no-compile','--only-binary=:all:','--require-hashes','--find-links',str(args.wheelhouse.resolve()),'-r',str(requirements)])
    if args.gate:
        run('release-blocking-ci',[sys.executable,'-B','scripts/run_test_profile.py','release-blocking-ci','--json','--output-root',str(work/'gate')])
    if args.native:
        if os.name!='nt':
            raise ValueError('Native execution requires Windows')
        from scripts.build_native_distribution import build
        artifact=build(work/'artifacts',args.wheelhouse.resolve(),release_validation_source=args.source_commit,release_validation_tree=args.source_tree)
        save(work/'native-build.json',artifact)
        guard_base=str(next(p for p in work.parents if p.name in {'l7-a2','l7-a3','l7-a4','l7-a6'}))
        run('native-acceptance',[sys.executable,'-B','scripts/accept_native_distribution.py','--zip',str(work/'artifacts'/artifact['filename']),'--python',sys.executable,'--run',str(work/'native acceptance'),'--guard-base',guard_base])
    save(work/'result.json',{'status':'PASS','source_commit':args.source_commit,'source_tree':args.source_tree,'gate_executed':args.gate,'native_executed':args.native,'genuine_windows11_acceptance_claimed':False,'validation_only':True})


if __name__=='__main__':
    main()
