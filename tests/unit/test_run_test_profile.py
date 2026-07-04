from __future__ import annotations

import json
import subprocess

import pytest

import scripts.run_test_profile as rtp


@pytest.mark.parametrize('profile', ['fast','default-ci','full-non-network','operator-preflight','browser-e2e'])
def test_known_profile_resolution(profile):
    commands = rtp.resolve_profile(profile)
    assert commands
    assert all(cmd[0] for cmd in commands)


def test_unknown_profile_fails_closed():
    with pytest.raises(ValueError, match='Unknown test profile'):
        rtp.resolve_profile('surprise-live')


def test_bounded_live_requires_explicit_confirmation():
    with pytest.raises(ValueError, match='requires --confirm-bounded-live'):
        rtp.resolve_profile('bounded-live')


def test_invalid_ssl_policy_fails_closed():
    with pytest.raises(ValueError, match='Invalid ssl_policy'):
        rtp.resolve_profile('fast', ssl_policy='silent-fallback')


@pytest.mark.parametrize('profile', ['fast','default-ci'])
def test_non_live_pytest_profiles_do_not_route_to_browser_or_live(profile):
    rendered = '\n'.join(rtp.command_to_display(cmd) for cmd in rtp.resolve_profile(profile))
    assert 'run_m6g_browser_operator_e2e.py' not in rendered
    assert '--execute-bounded-live-check' not in rendered


def test_operator_preflight_resolves_authoritative_runners():
    rendered = [rtp.command_to_display(cmd) for cmd in rtp.resolve_profile('operator-preflight')]
    assert any('run_m6e_operator_acceptance.py --check-only' in c for c in rendered)
    assert any('run_operator_preflight.py --json --timeout-seconds 300' in c for c in rendered)
    assert any('server/mcp_server.py --startup-check' in c for c in rendered)
    assert any('governance_forbidden_path_guard.py' in c for c in rendered)
    assert any('forbidden_behavior_scanner.py' in c for c in rendered)


def test_browser_and_bounded_live_resolve_m6g_modes():
    browser = rtp.command_to_display(rtp.resolve_profile('browser-e2e')[0])
    bounded = rtp.command_to_display(rtp.resolve_profile('bounded-live', confirm_bounded_live=True, ssl_policy='compatibility')[0])
    assert 'run_m6g_browser_operator_e2e.py --check-only' in browser
    assert 'run_m6g_browser_operator_e2e.py --execute-bounded-live-check --ssl-policy compatibility' in bounded


def test_json_output_contract(monkeypatch, capsys):
    def fake_run(cmd, cwd, text, stdout, stderr):
        return subprocess.CompletedProcess(cmd, 0, '============================= test session starts ==============================\ncollected 3 items\n\ntests/unit/test_x.py ...\n============================== 3 passed in 0.01s ===============================\n')
    monkeypatch.setattr(rtp.subprocess, 'run', fake_run)
    assert rtp.main(['fast', '--json']) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload['profile'] == 'fast'
    assert payload['status'] == 'pass'
    assert payload['commands']
    assert payload['network_may_have_occurred'] is False
    assert payload['browser_required'] is False
    assert payload['explicit_live_confirmation'] is False
    assert payload['ssl_policy'] == 'strict'
    assert payload['collected'] == 3
    assert payload['selected'] == 3
    assert payload['passed'] == 3
