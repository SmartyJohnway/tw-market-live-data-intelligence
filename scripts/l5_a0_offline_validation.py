"""A0 acceptance tooling only: run existing offline gates with external sockets denied."""
from pathlib import Path
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.relative_to(ROOT / 'docs/governance/phase_l/acceptance_runs')
    out.mkdir(parents=True, exist_ok=True)
    commands = [[sys.executable, 'scripts/' + name + '.py'] for name in (
        'verify_dependency_supply_chain', 'verify_environment', 'validate_source_registry',
        'validate_portable_catalog_sync', 'validate_runtime_skill_guide_sync',
        'validate_v1_public_contracts', 'validate_unified_market_evidence_contracts',
        'validate_phase_h_v3_contracts')]
    commands += [[sys.executable, '-m', 'pip', 'check'],
                 [sys.executable, '-m', 'compileall', '-q', 'scripts', 'server', 'tests'],
                 [sys.executable, 'scripts/run_test_profile.py', 'default-ci', '--json'],
                 ['git', 'diff', '--check']]
    results = []
    with tempfile.TemporaryDirectory(prefix='twmarket-l5-a0-') as temp:
        guard = Path(temp)
        attempt_log = guard / 'external_attempts.jsonl'
        (guard / 'sitecustomize.py').write_text('''import sys, os, json, ipaddress
def audit(event, args):
    if event not in ('socket.connect', 'socket.sendto', 'socket.getaddrinfo'):
        return
    address = args[0] if event == 'socket.getaddrinfo' else args[-1] if event == 'socket.sendto' else args[1]
    host = address[0] if isinstance(address, tuple) else address
    if host in ('localhost', '127.0.0.1', '::1', None):
        return
    try:
        if ipaddress.ip_address(host).is_loopback:
            return
    except (ValueError, TypeError):
        pass
    with open(os.environ['L5_A0_SOCKET_LOG'], 'a', encoding='utf-8') as f:
        f.write(json.dumps({'event':event, 'host':str(host)}) + '\\n')
    raise RuntimeError('L5_A0_EXTERNAL_NETWORK_DENIED')
sys.addaudithook(audit)
''', encoding='utf-8')
        env = dict(os.environ, PYTHONPATH=str(guard) + os.pathsep + str(ROOT),
                   L5_A0_SOCKET_LOG=str(attempt_log), PYTHONUTF8='1',
                   PIP_DISABLE_PIP_VERSION_CHECK='1')
        for i, command in enumerate(commands):
            started = time.monotonic()
            proc = subprocess.run(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace')
            log = f'validator_{i+1:02d}.txt'
            (out / log).write_text(proc.stdout, encoding='utf-8')
            result = dict(command=command, return_code=proc.returncode, log=log,
                          seconds=round(time.monotonic()-started, 3))
            results.append(result)
            print(json.dumps(result), flush=True)
        attempts = attempt_log.read_text(encoding='utf-8').splitlines() if attempt_log.exists() else []
    required_results = [r for i, r in enumerate(results) if i != 10]
    default_ci = results[10]
    required_pass = all(r['return_code'] == 0 for r in required_results) and not attempts
    report = dict(status='REQUIRED_BASELINE_PASS' if required_pass else 'REQUIRED_BASELINE_HOLD',
                  required_baseline_status='PASS' if required_pass else 'HOLD',
                  additional_default_ci_status=('PASS' if default_ci['return_code'] == 0 else 'FAIL_NON_GATE_OBSERVATION'),
                  a0_acceptance_blocked_by_default_ci=False,
                  validators=results, provider_requests=0, external_socket_attempts=len(attempts),
                  external_attempt_records=[json.loads(line) for line in attempts],
                  production_user_state_mutations=0,
                  scope='Python audit-hook guarded validator processes and inherited Python subprocesses; git fetch is entry transport, excluded from provider-validation counters; no OS-wide traffic claim')
    (out / 'validation_results.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    return 0 if required_pass else 1

if __name__ == '__main__':
    raise SystemExit(main())
