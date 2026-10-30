"""S2 source onboarding: real CLI processes, fresh state, no external network.

The child-only audit guard is test containment, not a product firewall. It is
inherited by Python descendants through sitecustomize; production is unchanged.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[2]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


GUARD = r'''
import ipaddress, json, os, shlex, sys, weakref
from pathlib import Path
bound = os.path.normcase(os.path.abspath(os.environ['S2_BOUND']))
fences = json.loads(os.environ['S2_FENCES'])
original_open = open
bound_sockets = weakref.WeakSet()
def record(event, **fields):
    with original_open(os.environ['S2_AUDIT'], 'a', encoding='utf-8') as f:
        f.write(json.dumps(dict(event=event, pid=os.getpid(), **fields)) + '\n')
def below(value, root):
    return value == root or value.startswith(root + os.sep)
def reject(reason):
    record('denied', reason=reason)
    raise PermissionError('S2_' + reason)
def check(path, write=False):
    if not isinstance(path, (str, bytes, os.PathLike)): return
    value = os.path.normcase(os.path.abspath(os.fsdecode(path)))
    if value == os.path.normcase(os.devnull): return
    if any(below(value, os.path.normcase(os.path.abspath(p))) for p in fences):
        reject('REAL_OR_DECOY_STATE_ACCESS')
    if write and not below(value, bound): reject('WRITE_OUTSIDE_DISPOSABLE_ROOT')
def loopback(host):
    if host == 'localhost': return True
    try: return ipaddress.ip_address(host).is_loopback
    except ValueError: return False
def owned_pair(address):
    # Windows asyncio's socketpair connects to its own just-bound loopback listener.
    for sock in list(bound_sockets):
        try:
            if sock.getsockname() == address: return True
        except OSError: pass
    return False
def audit(event, args):
    if event == 'open':
        check(args[0], bool(args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)))
    elif event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.utime', 'os.truncate'):
        check(args[0], True)
    elif event in ('os.rename', 'os.link', 'os.symlink'):
        check(args[0], True); check(args[1], True)
    elif event in ('os.listdir', 'os.scandir', 'os.chdir'): check(args[0])
    elif event in ('socket.connect', 'socket.bind', 'socket.sendto', 'socket.getaddrinfo'):
        address = args[0] if event == 'socket.getaddrinfo' else args[1]
        host = address[0] if isinstance(address, tuple) else address
        if not loopback(host): reject('EXTERNAL_NETWORK')
        if event == 'socket.bind' and isinstance(address, tuple) and address[1] == 0:
            bound_sockets.add(args[0])
        if (event in ('socket.connect', 'socket.sendto') and os.environ.get('S2_SERVICE_PORT')
                and (not isinstance(address, tuple) or address[1] != int(os.environ['S2_SERVICE_PORT']))
                and not owned_pair(address)):
            reject('UNSELECTED_LOOPBACK_SERVICE')
        record('loopback', operation=event)
    elif event == 'subprocess.Popen':
        child_env = args[3]
        if child_env is not None and any(child_env.get(k) != os.environ.get(k) for k in
                ('PYTHONPATH', 'S2_BOUND', 'S2_FENCES', 'S2_AUDIT', 'S2_SERVICE_PORT')):
            reject('UNGUARDED_CHILD')
        executable = args[0]
        if executable is None:
            executable = (args[1][0] if isinstance(args[1], (list, tuple))
                          else shlex.split(args[1], posix=False)[0].strip('"'))
        if os.path.normcase(os.path.abspath(executable)) != os.path.normcase(os.path.abspath(sys.executable)):
            reject('UNGUARDED_CHILD')
        record('python_child')
    elif event in ('os.system', 'os.startfile', 'os.startfile/2', 'os.posix_spawn'):
        reject('UNGUARDED_CHILD')
sys.addaudithook(audit)
for name in ('stat', 'lstat', 'readlink'):
    original = getattr(os, name)
    def guarded(path, *a, _original=original, **kw):
        check(path)
        return _original(path, *a, **kw)
    setattr(os, name, guarded)
record('guard_loaded')
'''


def isolated_environment(root: Path) -> dict[str, str]:
    root.mkdir()
    env = dict(os.environ)
    fences = [str(Path(env['LOCALAPPDATA']) / 'TW-Market')] if env.get('LOCALAPPDATA') else []
    for name in ('TW_MARKET_HOME', 'TW_MARKET_STATE_ROOT', 'TW_MARKET_SECURITY_MASTER_ROOT',
                 'TW_MARKET_WATCHLIST_ROOT', 'M8R_06_03_CONTROL_ROOT'):
        if env.get(name):
            fences.append(env[name])
    for name in list(env):
        if (name.startswith(('TW_MARKET_', 'M8R_', 'A6_')) or name in
                {'UNIFIED_MARKET_EVIDENCE_SERVICE_URL', 'PYTEST_ADDOPTS', 'PYTHONPATH', 'PYTHONHOME'}
                or name.lower() in {'http_proxy', 'https_proxy', 'all_proxy'}):
            env.pop(name)
    for name, part in {'TW_MARKET_HOME': 'installation', 'TW_MARKET_STATE_ROOT': 'state',
                       'LOCALAPPDATA': 'local', 'TEMP': 'temp', 'TMP': 'temp',
                       'HOME': 'user', 'USERPROFILE': 'user', 'APPDATA': 'roaming'}.items():
        env[name] = str(root / part)
    for part in ('local', 'temp', 'user', 'roaming', 'guard'):
        (root / part).mkdir()
    (root / 'guard/sitecustomize.py').write_text(GUARD, encoding='utf-8')
    env.update(S2_BOUND=str(root), S2_FENCES=json.dumps(fences), S2_AUDIT=str(root / 'audit.jsonl'),
               PYTHONPATH=str(root / 'guard') + os.pathsep + str(ROOT),
               PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    return env


def command(env, *args, expected=0):
    audit_path = Path(env['S2_AUDIT'])
    before = audit_path.read_text().count('"guard_loaded"') if audit_path.exists() else 0
    proc = subprocess.run([sys.executable, '-B', *args], cwd=ROOT, env=env,
                          capture_output=True, text=True, encoding='utf-8', timeout=45)
    assert audit_path.read_text().count('"guard_loaded"') > before, 'child containment did not load'
    assert proc.returncode == expected, (args, proc.returncode, proc.stdout, proc.stderr)
    return proc


def events(env):
    return [json.loads(line) for line in Path(env['S2_AUDIT']).read_text().splitlines()]


def test_isolated_source_first_run(tmp_path):
    root = tmp_path / 'source-first-run'
    env = isolated_environment(root)
    # Even status/preflight must not inspect a developer's service on port 8000.
    with socket.socket() as reservation:
        reservation.bind(('127.0.0.1', 0))
        port = reservation.getsockname()[1]
    env.update(TW_MARKET_HOST='127.0.0.1', TW_MARKET_PORT=str(port), S2_SERVICE_PORT=str(port))
    url = f'http://127.0.0.1:{port}'
    evidence = {'commands': [], 'isolated_variables': {n: env[n] for n in (
        'TW_MARKET_HOME', 'TW_MARKET_STATE_ROOT', 'LOCALAPPDATA', 'TEMP', 'TMP',
        'HOME', 'USERPROFILE', 'APPDATA', 'TW_MARKET_HOST', 'TW_MARKET_PORT')},
        'external_network': 'FORBIDDEN'}

    def cli(*args, expected=0):
        p = command(env, *args, expected=expected)
        evidence['commands'].append({'args': list(args), 'exit': p.returncode,
                                     'stdout': p.stdout, 'stderr': p.stderr})
        return p

    assert not Path(env['TW_MARKET_HOME']).exists() and not Path(env['TW_MARKET_STATE_ROOT']).exists()
    assert json.loads(cli('scripts/verify_environment.py').stdout)['status'] == 'PASS'
    cli('scripts/validate_phase_h_v3_contracts.py')
    pre = json.loads(cli('scripts/tw_market_lifecycle.py', 'status', '--json').stdout)
    assert pre['status'] == 'INSTALLATION_NOT_INITIALIZED'
    assert not Path(env['TW_MARKET_HOME']).exists()
    cli('scripts/run_unified_workbench.py', '--startup-check', expected=1)
    cli('scripts/run_unified_market_evidence_mcp.py', '--startup-check', expected=2)

    init_args = ('scripts/tw_market_lifecycle.py', 'init', '--home', env['TW_MARKET_HOME'],
                 '--state-root', env['TW_MARKET_STATE_ROOT'], '--json')
    first = json.loads(cli(*init_args).stdout)
    assert first['status'] == 'INSTALLATION_READY'
    assert first['installation']['installation_status'] == 'READY'
    assert first['identity']['status'] == 'NOT_INITIALIZED' and first['network_on_init'] is False
    assert first['installation']['home'] == env['TW_MARKET_HOME']
    assert first['installation']['state_root'] == env['TW_MARKET_STATE_ROOT']
    initial_files = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for base in ('installation', 'state') for p in (root / base).rglob('*') if p.is_file()}
    assert set(initial_files) == {'installation/config/settings.json', 'installation/meta/installation.json'}
    for directory in ('security-master', 'watchlists', 'governed'):
        assert (root / 'state' / directory).is_dir()
    second = json.loads(cli(*init_args).stdout)
    assert first['installation']['installation_id'] == second['installation']['installation_id']
    assert initial_files == {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                             for base in ('installation', 'state') for p in (root / base).rglob('*') if p.is_file()}
    sm = json.loads(cli('scripts/manage_security_master.py', 'status').stdout)
    assert sm['status'] == 'NOT_INITIALIZED'
    status = json.loads(cli('scripts/tw_market_lifecycle.py', 'status', '--json').stdout)
    assert status['installation']['installation_status'] == 'READY'
    assert status['identity']['status'] == 'NOT_INITIALIZED'
    assert status['service']['port'] == port and not status['service']['alive']
    preload = json.loads(cli('scripts/run_unified_workbench.py', '--startup-check').stdout)
    assert preload['security_master_status'] == 'NOT_INITIALIZED'
    assert preload['canonical_schema_loaded'] and preload['capability_catalog_loaded']
    assert not preload['network_on_startup'] and not preload['security_master_loaded']

    cli('scripts/run_unified_market_evidence_mcp.py', '--service-url', url, '--startup-check', expected=3)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    service_args = ['scripts/run_unified_workbench.py', '--host', '127.0.0.1', '--port', str(port)]
    with (root / 'service.log').open('w', encoding='utf-8') as log:
        proc = subprocess.Popen([sys.executable, '-B', *service_args], cwd=ROOT, env=env,
                                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        evidence['service'] = {'args': service_args, 'pid': proc.pid}
        try:
            deadline = time.monotonic() + 25
            while True:
                assert proc.poll() is None, (root / 'service.log').read_text()
                try:
                    with opener.open(url + '/api/health', timeout=1) as response:
                        assert response.status == 200
                        evidence['health'] = json.load(response)
                    break
                except (urllib.error.URLError, TimeoutError):
                    assert time.monotonic() < deadline, 'loopback service readiness timeout'
                    time.sleep(.1)
            with opener.open(url + '/workbench/', timeout=5) as response:
                assert response.status == 200 and b'<html' in response.read().lower()
                evidence['workbench_status'] = response.status
            capabilities = urllib.request.Request(url + '/api/unified/capabilities', headers={
                'X-TW-Market-Service-Contract': 'unified_market_evidence_local_service.v2'})
            with opener.open(capabilities, timeout=5) as response:
                evidence['service_contract'] = json.load(response)['service_contract_version']
                assert evidence['service_contract'] == 'unified_market_evidence_local_service.v2'
            request = {'request': {'schema_version': 'unified_market_evidence_request.v3',
                                   'request_id': 's2-fresh-source', 'execution_mode': 'preview',
                                   'targets': [{'input': '2330'}],
                                   'data_needs': [{'type': 'identity', 'priority': 'required'}]}}
            import jsonschema
            jsonschema.Draft7Validator(json.loads((ROOT / 'schemas/unified_market_evidence_request.v3.schema.json').read_text())).validate(request['request'])
            req = urllib.request.Request(url + '/api/unified/validate-request',
                                         data=json.dumps(request).encode(), headers={'Content-Type': 'application/json'})
            try:
                opener.open(req, timeout=5)
                raise AssertionError('identity-dependent validation must fail closed')
            except urllib.error.HTTPError as exc:
                assert exc.code == 503
                evidence['identity_failure'] = json.load(exc)
                assert evidence['identity_failure']['error'] == 'SECURITY_MASTER_NOT_INITIALIZED'
            cli('scripts/run_unified_market_evidence_mcp.py', '--service-url', url, '--startup-check')
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
            evidence['service']['terminated'] = proc.poll() is not None
    assert evidence['service']['terminated']
    with socket.socket() as probe:
        assert probe.connect_ex(('127.0.0.1', port)) != 0
    assert not any(p.is_file() for p in (root / 'state/security-master').rglob('*'))
    audit = events(env)
    assert not [e for e in audit if e['event'] == 'denied']
    assert proc.pid in {e['pid'] for e in audit if e['event'] == 'guard_loaded'}
    evidence.update(created_files=sorted(str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()),
                    final_identity_status='NOT_INITIALIZED', final_installation_status='READY',
                    guard_events=len(audit), guard_denials=0)
    (root / 'smoke-evidence.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')


def test_isolation_guard_and_existing_default_cannot_satisfy_fresh_state(tmp_path):
    env = isolated_environment(tmp_path / 'leakage')
    decoy = Path(env['LOCALAPPDATA']) / 'TW-Market'
    command({**env, 'TW_MARKET_HOME': str(decoy), 'TW_MARKET_STATE_ROOT': str(decoy / 'state')},
            'scripts/tw_market_lifecycle.py', 'init', '--json')
    env['S2_FENCES'] = json.dumps(json.loads(env['S2_FENCES']) + [str(decoy)])
    env['S2_SERVICE_PORT'] = '1'
    # Guard is installed before the CLI, and must not fall back to the existing default.
    result = command(env, 'scripts/run_unified_workbench.py', '--startup-check', expected=1)
    assert json.loads(result.stdout)['reason_code'] == 'INSTALLATION_NOT_INITIALIZED'
    assert not Path(env['TW_MARKET_HOME']).exists()
    for source in (f'open({str(decoy / "meta/installation.json")!r})',
                   f'__import__("os").stat({str(decoy)!r})',
                   '__import__("socket").create_connection(("198.51.100.1", 443))',
                   '__import__("socket").create_connection(("127.0.0.1", 8000))',
                   'import subprocess,sys; subprocess.run([sys.executable,"-c","pass"],env={})'):
        p = command(env, '-c', source, expected=1)
        assert 'PermissionError: S2_' in p.stderr
    denied = [e['reason'] for e in events(env) if e['event'] == 'denied']
    assert denied == ['REAL_OR_DECOY_STATE_ACCESS', 'REAL_OR_DECOY_STATE_ACCESS',
                      'EXTERNAL_NETWORK', 'UNSELECTED_LOOPBACK_SERVICE', 'UNGUARDED_CHILD']


def test_source_start_documents_link_to_initialized_service_topology():
    """Protect startup commands/order and navigation, not document fingerprints."""
    primary = (ROOT / 'docs/operator/QUICK_START.md').read_text(encoding='utf-8')
    source = primary.split('<a id="source-first-run"></a>', 1)[1].split('## Governed product flow', 1)[0]
    ordered = ['scripts/verify_environment.py', 'scripts/tw_market_lifecycle.py init',
               'scripts/run_unified_workbench.py --startup-check',
               'scripts/run_unified_workbench.py --host 127.0.0.1',
               'scripts/run_unified_market_evidence_mcp.py --service-url']
    positions = [source.index(command) for command in ordered]
    assert positions == sorted(positions)
    assert 'INSTALLATION_READY' in source and 'SECURITY_MASTER_NOT_INITIALIZED' in source
    for name in ('README.md', 'README.zh-TW.md', 'docs/operator/LOCAL_WORKBENCH.md',
                 'docs/operator/MODE_ABC_WALKTHROUGH.md', 'docs/operator/TROUBLESHOOTING.md',
                 'docs/operator/M8R_08B_MCP_LOCAL_CLIENT.md', 'docs/reference/API_REFERENCE.md',
                 'docs/reference/MCP_REFERENCE.md', 'docs/distribution/MCP_DISTRIBUTION.md'):
        assert 'QUICK_START.md#source-first-run' in (ROOT / name).read_text(encoding='utf-8'), name
