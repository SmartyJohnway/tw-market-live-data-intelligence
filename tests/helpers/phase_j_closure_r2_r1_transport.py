"""Acceptance-only missing exchange timestamp at the raw HTTP fixture boundary."""
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

def install():
    from tests.helpers.phase_j_closure_r1_transport import install as install_base
    install_base()
    import urllib.request
    original = urllib.request.urlopen

    def raw(request, **kwargs):
        response = original(request, **kwargs)
        payload = json.loads(response.read())
        if request.full_url.startswith('https://mis.twse.com.tw/stock/api/getStockInfo.jsp?'):
            for row in payload['msgArray']:
                row.pop('d', None)
                row.pop('t', None)
        class Response(io.BytesIO):
            status = 200
            headers = {'Content-Type': 'application/json'}
        return Response(json.dumps(payload).encode())

    urllib.request.urlopen = raw

if __name__ == '__main__':
    from scripts import m8r_06_03_execute_once as wrapper
    wrapper._install_deterministic_test_transport = install
    raise SystemExit(wrapper.main())
