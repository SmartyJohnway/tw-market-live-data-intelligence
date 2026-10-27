import json
from pathlib import Path
import subprocess
import sys

import pytest

from scripts import accept_l7_a2_docker as docker
from scripts import run_l7_a2_release_validation as release_validation
from scripts import run_test_profile
from scripts import run_v1_release_readiness as readiness


def test_canonical_runner_starts_with_bytecode_suppressed(tmp_path):
    commands = run_test_profile.resolve_profile('release-blocking-ci', output_root=tmp_path)
    assert len(commands) == 1
    cmd = commands[0]
    assert cmd[:3] == [sys.executable, '-B', 'scripts/run_deterministic_ci.py']
    assert cmd[-2:] == ['--output-root', str(tmp_path / 'release-blocking-ci')]
    assert subprocess.check_output(cmd[:2] + ['-c', 'import sys; print(sys.dont_write_bytecode)'], text=True).strip() == 'True'


@pytest.mark.parametrize('scope', ['l7-a2', 'l7-a3', 'l7-a4', 'l7-a6'])
def test_existing_and_new_windows_validation_scopes(scope):
    assert release_validation.authorized_windows_workspace(Path(r'C:\twmarket_temp') / scope / 'nested')
    assert scope in docker.VALIDATION_SCOPES


@pytest.mark.parametrize('path', [r'C:\twmarket_temp\other\x', 'C:\\', r'C:\Users\person\AppData\Local\TW-Market', r'C:\twmarket_temp\l7-a60\x', r'D:\twmarket_temp\l7-a6\x'])
def test_unapproved_windows_workspaces_are_rejected(path):
    assert not release_validation.authorized_windows_workspace(Path(path))


def test_docker_cli_advertises_a6_without_executing_docker(capsys, monkeypatch):
    monkeypatch.setattr(sys, 'argv', ['accept_l7_a2_docker.py', '--help'])
    with pytest.raises(SystemExit) as exc:
        docker.main()
    assert exc.value.code == 0
    assert 'l7-a6' in capsys.readouterr().out


def _stub_readiness(monkeypatch, fail_diagnostics=True):
    calls = []
    monkeypatch.setattr(readiness, 'git_clean', lambda: True)
    monkeypatch.setattr(readiness, 'git_value', lambda *args: 'a' * 40)
    def fake_run(name, command, **kwargs):
        calls.append((name, command))
        failed = fail_diagnostics and name in {'default_ci', 'full_non_network'}
        return {'name': name, 'command': command, 'status': 'FAIL' if failed else 'PASS', 'return_code': 1 if failed else 0}
    monkeypatch.setattr(readiness, 'run', fake_run)
    monkeypatch.setattr(readiness, 'javascript_syntax', lambda out: {'status': 'PASS'})
    monkeypatch.setattr(readiness, 'source_archive_smoke', lambda out: {'status': 'PASS'})
    return calls


def test_readiness_blocks_on_canonical_and_preserves_failed_diagnostics(tmp_path, monkeypatch):
    calls = _stub_readiness(monkeypatch)
    out = tmp_path / 'fresh'
    assert readiness.main(['--output-root', str(out)]) == 0
    report = json.loads((out / 'v1_release_readiness.json').read_text(encoding='utf-8'))
    gate = next(g for g in report['gates'] if g['name'] == 'release_blocking_ci')
    assert gate['status'] == 'PASS' and 'release-blocking-ci' in gate['command']
    assert {r['name']: r['status'] for r in report['diagnostics']} == {'default_ci': 'FAIL', 'full_non_network': 'FAIL'}
    assert report['status'] == 'PASS'
    assert report['browser_e2e']['status'] == 'NOT_REQUESTED_BY_RELEASE_PLAN'
    assert all(name != 'browser_e2e' for name, _ in calls)


def test_readiness_canonical_failure_blocks(tmp_path, monkeypatch):
    _stub_readiness(monkeypatch, fail_diagnostics=False)
    old = readiness.run
    def fake(name, command, **kwargs):
        if name == 'release_blocking_ci':
            return {'name': name, 'status': 'FAIL', 'return_code': 1}
        return old(name, command, **kwargs)
    monkeypatch.setattr(readiness, 'run', fake)
    out = tmp_path / 'fresh'
    assert readiness.main(['--output-root', str(out)]) == 1
    report = json.loads((out / 'v1_release_readiness.json').read_text(encoding='utf-8'))
    assert report['status'] == 'FAIL'


def test_browser_is_blocking_only_when_explicitly_requested(tmp_path, monkeypatch):
    calls = _stub_readiness(monkeypatch, fail_diagnostics=False)
    out = tmp_path / 'fresh'
    assert readiness.main(['--output-root', str(out), '--require-browser-e2e']) == 0
    report = json.loads((out / 'v1_release_readiness.json').read_text(encoding='utf-8'))
    assert report['browser_e2e']['status'] == 'PASS'
    assert any(name == 'browser_e2e' for name, _ in calls)


def test_readiness_rejects_reused_evidence_directory(tmp_path):
    existing = tmp_path / 'used'
    existing.mkdir()
    with pytest.raises(FileExistsError):
        readiness.main(['--output-root', str(existing)])