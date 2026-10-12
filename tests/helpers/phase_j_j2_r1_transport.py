"""Synthetic, network-free, acceptance-only raw transport for real orchestration.

Executed only by the external test server's child wrapper. No route, builder,
normalizer, renderer, authorization or MCP handler is substituted.
"""
from pathlib import Path
import calendar
import json
import os
import sys
from datetime import date, datetime, timezone
from uuid import uuid4
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

def install():
    assert os.environ['M8R_06_03_EXECUTION_ENVIRONMENT'] == 'test'
    assert os.environ['M8R_06_03_TEST_SOURCE_TRANSPORT'] == 'deterministic'
    from scripts import m8r_06_03_production_adapter as adapter
    from server.services import phase_h_h1_tpex_composite as h1
    from server.services import phase_h_h2_twse_exright_executor as h2
    from server.services import phase_h_h3_twse_stock_day_adapter as h3
    from tests.unit.test_phase_h_h3_i2a_twse_stock_day_adapter import _html, _row, FakeResponse
    scenario = os.environ['PHASE_J_R1_SCENARIO']
    def count(source):
        root = Path(os.environ['M8R_06_03_TEST_INVOCATION_COUNTER'])
        root.mkdir(parents=True, exist_ok=True)
        (root / f'{source}-{uuid4().hex}.invoked').write_text('synthetic network-free acceptance-only')
    def research(url, *, timeout):
        count('research')
        if scenario in ('J1-20', 'J1-23'): return b'[]' if 'json' in url.lower() else b''
        code = '2317' if scenario in ('J1-07','J1-22') else '2330'
        subject = '更正合成測試公告' if scenario == 'J1-08' else '合成測試公告'
        return f'出表日期,公司代號,公司名稱,發言日期,發言時間,主旨,說明\n1151011,{code},合成公司,1151010,100000,{subject},synthetic network-free acceptance-only\n'.encode()
    adapter._fetch_official_payload = research
    fixture = json.loads((ROOT/'tests/fixtures/phase_h_h1_adapters/source_rows.json').read_text())
    def h1_get(endpoint, **kwargs):
        count('h1')
        rows = fixture['tpex_attention'] if 'warning' in endpoint else fixture['tpex_disposition'] if 'disposal' in endpoint else []
        return dict(raw_bytes=json.dumps(rows).encode(), status=200, content_type='application/json', effective_url=endpoint, retrieved_at=datetime.now(timezone.utc).isoformat(), tls_policy='compatibility', redirect_count=0)
    h1.official_get = h1_get
    def stock(request, timeout_seconds, **kwargs):
        from urllib.parse import parse_qs, urlsplit
        count('h3')
        query = parse_qs(urlsplit(request.full_url).query)
        token = query['date'][0]
        year, month = int(token[:4]), int(token[4:6])
        rows = [_row(f'{year-1911}/{month:02d}/{day:02d}', close='1,440.00') for day in range(1,calendar.monthrange(year,month)[1]+1) if date(year,month,day).weekday()<5 and date(year,month,day)<date.today()]
        return FakeResponse(_html(*rows,title=f'{year-1911}年{month:02d}月 2330 合成公司 各日成交資訊'))
    h3._default_http_get = stock
    def h2_get(**kwargs):
        count('h2')
        return dict(raw_bytes=b'[]',status=200,content_type='application/json',effective_url=h2.ENDPOINT,retrieved_at=datetime.now(timezone.utc).isoformat())
    h2.official_get_once = h2_get
    from server.services import phase_i_i2_production_candidate as i2
    from scripts.run_phase_i_i2_a3_bounded_live_acceptance import deterministic_fixture_payload
    def i2_get(url, timeout):
        count('i2')
        return 200, {'Content-Type':'application/json'}, deterministic_fixture_payload()
    i2._read_once = i2_get

if __name__ == '__main__':
    from scripts import m8r_06_03_execute_once as wrapper
    original = wrapper._install_deterministic_test_transport
    def combined():
        original()
        install()
    wrapper._install_deterministic_test_transport = combined
    raise SystemExit(wrapper.main())
