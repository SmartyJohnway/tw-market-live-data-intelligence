"""Acceptance-only child transport; actual fixed execute-once protocol is reused.

Follows tests/helpers/phase_j_closure_r1_transport.py. No runtime dispatch,
normalization, evidence, Result, Audit or handoff is replaced.
"""
from pathlib import Path
import io
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def install():
    assert os.environ['M8R_06_03_EXECUTION_ENVIRONMENT'] == 'test'
    assert os.environ['M8R_06_03_TEST_SOURCE_TRANSPORT'] == 'deterministic'
    from scripts import m8r_06_03_production_adapter as adapter
    from tests.unit.test_phase_g_monthly_revenue import HEAD, ROW
    from tests.unit.test_phase_g_material_disclosures import CSV
    from scripts.phase_g.research_executor import ROUTES

    def audit(event, args):
        if event in {'socket.connect', 'socket.getaddrinfo', 'socket.sendto'}:
            if os.environ.get('L5_A6_SOCKET_LOG'):
                with Path(os.environ['L5_A6_SOCKET_LOG']).open('a', encoding='utf-8') as f:
                    f.write(json.dumps({'event':event,'blocked_before_dispatch':True})+'\n')
            raise AssertionError('A6_UNEXPECTED_CHILD_SOCKET:' + event)
    sys.addaudithook(audit)

    def raw(request, *, timeout):
        url = request.full_url
        code = os.environ['L5_A6_CODE']
        contract = next((r['contract'] for r in ROUTES.values() if url in (r['csv_url'],r['json_url'])), None)
        assert contract is not None, 'A6_UNKNOWN_SOURCE_URL'
        assert contract.endswith('_L' if code == '2330' else '_O'), 'A6_WRONG_MARKET_TRANSPORT'
        payload = (HEAD + ROW if 't187ap05' in contract else CSV).replace('2330', code).encode('utf-8')
        failed = os.environ['L5_A6_SCENARIO'] == 'mixed' and 't187ap04' in contract
        with Path(os.environ['L5_A6_TRANSPORT_LOG']).open('a', encoding='utf-8') as f:
            f.write(json.dumps({'url': url, 'contract': contract, 'timeout': timeout,
                                'fixture_payload_sha256':None if failed else hashlib.sha256(payload).hexdigest(),
                                'fixture_failure':failed,
                                'external_dispatch': False}) + '\n')
        if failed:
            raise OSError('A6 fixture source transport failure')
        return io.BytesIO(payload)
    adapter.urlopen = raw


if __name__ == '__main__':
    from scripts import m8r_06_03_execute_once as wrapper
    wrapper._install_deterministic_test_transport = install
    raise SystemExit(wrapper.main())
