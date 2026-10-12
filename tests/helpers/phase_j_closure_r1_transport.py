"""Synthetic/network-free/acceptance-only raw HTTP boundary; real adapters run."""
from pathlib import Path
import io,json,os,sys,time
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))

def load_source_rows_fixture():
    return json.loads((ROOT/'tests/fixtures/phase_j/closure_r1/source_rows.json').read_text(encoding='utf-8'))

def install():
    assert os.environ['M8R_06_03_EXECUTION_ENVIRONMENT']=='test'
    assert os.environ['M8R_06_03_TEST_SOURCE_TRANSPORT']=='deterministic'
    import urllib.request
    from scripts import m8r_06_03_production_adapter as a, m5k_common as mis
    from scripts import m8a_twse_official_eod_adapter as twse,m8a_tpex_official_eod_adapter as tpex
    # Restore genuine adapters replaced by the older generic fixture installer.
    a.execute_live_observation=mis.execute_live_observation
    a.execute_twse_official_eod_adapter=twse.execute_twse_official_eod_adapter
    a.execute_tpex_official_eod_adapter=tpex.execute_tpex_official_eod_adapter
    scenario=os.environ['PHASE_J_CLOSURE_R1_SCENARIO']
    fixture=load_source_rows_fixture()
    mis.utc_now=lambda:'2026-10-08T06:00:00Z'
    twse.utc_now=lambda:'2026-10-08T06:00:05Z'
    tpex.utc_now=lambda:'2026-10-08T06:00:05Z'
    class Response(io.BytesIO):
        status=200
        headers={'Content-Type':'application/json'}
    def raw(request,**kwargs):
        url=request.full_url
        if url.startswith('https://mis.twse.com.tw/stock/api/getStockInfo.jsp?'):
            row=dict(fixture['mis'])
            if scenario=='J1-21':row.update(d='20260901',t='13:30:00')
            payload={'rtcode':'0000','msgArray':[row]}
        elif url==twse.URL:payload=[fixture['twse']]
        elif url==tpex.URL:payload=[fixture['tpex']]
        else:raise AssertionError('UNEXPECTED_SOURCE_TRANSPORT')
        p=Path(os.environ['M8R_06_03_TEST_INVOCATION_COUNTER']);p.mkdir(parents=True,exist_ok=True)
        (p/f'{time.time_ns()}.invoked').write_text(json.dumps({'source_boundary':'raw_http_fixture','url':url,'method':'GET','external_dispatch':False}))
        return Response(json.dumps(payload).encode())
    urllib.request.urlopen=raw

if __name__=='__main__':
    from scripts import m8r_06_03_execute_once as wrapper
    wrapper._install_deterministic_test_transport=install
    raise SystemExit(wrapper.main())
