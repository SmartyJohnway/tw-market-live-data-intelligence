"""Offline structural, wheel-byte and import checks; no installation state initialization."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

from scripts.build_mcpb_distribution import ROOT, digest, inspect_wheels, validate_manifest
from packaging_native.path_scan import scan_payload
from packaging_mcpb.hygiene import scan, wheel_members
from packaging_mcpb.record import canonical_record


def accept(build_root: Path, wheelhouse: Path):
    report=json.loads((build_root/'build-report.json').read_bytes())
    archive=next(build_root.glob('*.mcpb'))
    if digest(archive.read_bytes()) != report['sha256']:
        raise ValueError('archive hash mismatch')
    upstream={}
    dependencies=inspect_wheels(wheelhouse)
    provenance=wheel_members(wheelhouse,dependencies)
    for d in dependencies:
        name=d['wheel_filename']; data=(wheelhouse/name).read_bytes()
        if scan_payload(name,data)['blocking']:
            raise ValueError('dependency hygiene failed: '+name)
        with zipfile.ZipFile(wheelhouse/name) as w:
            for n in w.namelist():
                if not n.endswith('/') and '.data/' not in n:
                    upstream[n]=digest(w.read(n))
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        if names != sorted(names) or len(names)!=len(set(n.casefold() for n in names)):
            raise ValueError('member ordering/duplicates')
        manifest=json.loads(z.read('manifest.json')); validate_manifest(manifest)
        final_lib={n[len('server/lib/'):]:z.read(n) for n in names if n.startswith('server/lib/')}
        if not set(upstream).issubset(final_lib):
            raise ValueError('accepted wheel member missing from dependency payload')
        for n,value in final_lib.items():
            if n.endswith('.dist-info/RECORD') and canonical_record(value,n,final_lib)[0]!=value:
                raise ValueError('installed RECORD is not canonical')
        mismatches=[]
        hygiene=[]
        for i in z.infolist():
            if i.date_time!=(1980,1,1,0,0,0) or i.create_system!=3 or i.external_attr != 0o100644 << 16:
                raise ValueError('ZIP normalization failed')
            data=z.read(i)
            hygiene.extend(scan(i.filename,data,provenance.get(i.filename)))
            if report['members'].get(i.filename) != digest(data):
                raise ValueError('member hash mismatch')
            if i.filename.startswith('server/lib/'):
                rel=i.filename[len('server/lib/'):]
                # pip writes deterministic installation metadata; original upstream bytes
                # remain bound individually. RECORD is installation-derived by pip.
                if rel.endswith(('/RECORD','/INSTALLER','/REQUESTED')):
                    if rel.endswith('/INSTALLER') and data!=b'pip\n':
                        raise ValueError('unexpected pip installer metadata')
                    if rel.endswith('/REQUESTED') and data!=b'':
                        raise ValueError('unexpected pip requested metadata')
                    continue
                if upstream.get(rel)!=digest(data):
                    mismatches.append(rel)
        if mismatches:
            raise ValueError('unexpected dependency bytes: '+','.join(mismatches[:3]))
        if any(row['blocking'] for row in hygiene):
            raise ValueError('artifact hygiene blocked; inspect redacted policy evidence')
    # --help imports the real launcher and its complete static contract closure,
    # then exits before installation resolution or Local Service access.
    env=dict(os.environ,PYTHONPATH=str(build_root/'install/server/lib')+os.pathsep+str(ROOT),PYTHONDONTWRITEBYTECODE='1')
    run=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/run_unified_market_evidence_mcp.py'),'--help'],
                       cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8')
    if run.returncode:
        raise ValueError('offline launcher import failed: '+run.stderr[-400:])
    return {'manifest':'PASS','exact_six':'PASS','dependency_completeness':'PASS',
            'wheel_input_count':49,'unexpected_dependency_sources':0,'offline_import':'PASS',
            'artifact_hygiene':'PASS','blocking_observations':0,'canonical_RECORD':'PASS',
            'network_requests':0,'purpose':'TEST_ONLY_NOT_FINAL_ACCEPTANCE'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--build-root',type=Path,required=True)
    p.add_argument('--wheelhouse',type=Path,required=True)
    a=p.parse_args(); print(json.dumps(accept(a.build_root,a.wheelhouse),sort_keys=True))
