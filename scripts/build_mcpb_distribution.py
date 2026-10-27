"""Build deterministic Windows MCPB from exact Git app and accepted offline wheels."""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import zipfile

import jsonschema

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_native_distribution import inspect_wheels, check_member
from packaging_mcpb.record import normalize_installed

TOOLS = {'market_describe_capabilities', 'market_validate_request', 'market_preview_request',
         'market_read_result', 'market_export_ai_handoff', 'market_fetch_evidence'}
FILENAME = 'tw-market-unified-mcp-v1.5.0-win-x64.mcpb'


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))+'\n').encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def canonical_tools():
    code = ast.parse(git('show', 'HEAD:server/unified_mcp/tool_contracts.py'))
    for node in code.body:
        if isinstance(node, ast.AnnAssign) and getattr(node.target, 'id', '') == 'TOOL_DESCRIPTIONS':
            names = set(ast.literal_eval(node.value))
            if names != TOOLS:
                raise ValueError('canonical exact-six tool authority changed')
            return names
    raise ValueError('canonical tool authority unavailable')


def manifest(version):
    result = json.loads((ROOT/'packaging_mcpb/manifest.template.json').read_bytes())
    result['version'] = version
    validate_manifest(result)
    return result


def validate_manifest(value):
    schema = json.loads((ROOT/'packaging_mcpb/upstream/mcpb-manifest-v0.3.schema.json').read_bytes())
    jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker()).validate(value)
    names = [t['name'] for t in value['tools']]
    if set(names) != canonical_tools() or len(names) != 6:
        raise ValueError('manifest exact-six disagreement')
    expected = ('0.3', '1.5.0', ['win32'], '>=3.13,<3.14')
    observed = (value['manifest_version'], value['version'], value['compatibility']['platforms'],
                value['compatibility']['runtimes']['python'])
    if observed != expected:
        raise ValueError('MCPB runtime/version disagreement')
    server = value['server']
    if server != json.loads((ROOT/'packaging_mcpb/manifest.template.json').read_bytes())['server']:
        raise ValueError('MCPB stdio launcher disagreement')


def write_archive(path, payload):
    with zipfile.ZipFile(path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for name, data in sorted(payload.items()):
            p = PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or ':' in name or '\\' in name:
                raise ValueError('unsafe ZIP member')
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def build(output, wheelhouse):
    output, wheelhouse = Path(output).resolve(), Path(wheelhouse).resolve()
    if output.is_relative_to(ROOT) or output.exists():
        raise ValueError('fresh external output required')
    if git('diff', 'HEAD', '--').strip():
        raise ValueError('clean tracked source required')
    version = git('show', 'HEAD:VERSION').decode().strip()
    if version != '1.5.0':
        raise ValueError('VERSION must be 1.5.0')
    try:
        deps = inspect_wheels(wheelhouse)
    except (ValueError, OSError) as exc:
        raise ValueError('MCPB_WHEELHOUSE_INCOMPLETE') from exc
    output.mkdir(parents=True)
    lib = output/'install'/'server'/'lib'
    req = output/'offline-requirements.txt'
    req.write_text(''.join(f"{d['name']}=={d['version']} --hash=sha256:{d['wheel_sha256']}\n" for d in deps), encoding='utf-8')
    env = dict(os.environ, PIP_NO_INDEX='1', PIP_DISABLE_PIP_VERSION_CHECK='1', PYTHONDONTWRITEBYTECODE='1')
    command = [sys.executable, '-B', '-m', 'pip', 'install', '--no-index', '--require-hashes', '--no-deps',
               '--no-compile', '--no-warn-script-location', '--only-binary=:all:', '--find-links', str(wheelhouse),
               '--target', str(lib), '-r', str(req)]
    run = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, encoding='utf-8')
    (output/'offline-install.log').write_text(run.stdout+run.stderr, encoding='utf-8')
    if run.returncode:
        raise ValueError('MCPB_OFFLINE_INSTALLATION_BLOCKED')
    record_normalization = normalize_installed(lib, wheelhouse, deps)
    payload = {}
    policy = json.loads(git('show', 'HEAD:packaging_native/resource-policy.json'))
    for entry in policy['members']:
        dest = entry['destination']
        if dest.startswith('app/'):
            data = git('show', 'HEAD:'+entry['source'])
            check_member(dest, data)
            payload[dest] = data
    for p in sorted(lib.rglob('*')):
        if not p.is_file():
            continue
        rel = p.relative_to(lib).as_posix()
        if rel.split('/')[0].lower() in {'bin', 'scripts'} or '__pycache__' in p.parts or p.suffix == '.pyc':
            continue
        payload['server/lib/'+rel] = p.read_bytes()
    payload['manifest.json'] = canonical(manifest(version))
    if 'app/scripts/run_unified_market_evidence_mcp.py' not in payload:
        raise ValueError('entrypoint missing')
    archive = output/FILENAME
    write_archive(archive, payload)
    sha = digest(archive.read_bytes())
    sidecar = output/(FILENAME+'.sha256')
    sidecar.write_bytes((sha+'  '+FILENAME+'\n').encode())
    result = {'purpose':'TEST_ONLY_NOT_FINAL_PUBLICATION_HASH', 'source_commit':git('rev-parse','HEAD').decode().strip(),
              'source_tree':git('rev-parse','HEAD^{tree}').decode().strip(), 'version':version,
              'wheelhouse_lock_sha256':digest((ROOT/'packaging_native/wheelhouse-lock.json').read_bytes()),
              'requirements_lock_sha256':digest((ROOT/'requirements-lock.txt').read_bytes()),
              'wheel_input_count':len(deps), 'network_dependency_requests':0,
              'record_normalization':record_normalization,
              'manifest_sha256':digest(payload['manifest.json']), 'member_count':len(payload),
              'bytes':archive.stat().st_size, 'sha256':sha,'sidecar_sha256':digest(sidecar.read_bytes()),
              'members':{n:digest(b) for n,b in sorted(payload.items())}}
    (output/'build-report.json').write_bytes(canonical(result))
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--wheelhouse',type=Path,required=True)
    a=p.parse_args()
    result=build(a.output,a.wheelhouse)
    print(json.dumps({k:v for k,v in result.items() if k!='members'},sort_keys=True))


if __name__ == '__main__':
    main()
