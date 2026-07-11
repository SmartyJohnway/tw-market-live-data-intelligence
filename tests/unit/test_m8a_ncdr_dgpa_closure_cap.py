from pathlib import Path
from scripts.m8a_ncdr_dgpa_closure_cap import parse_closure_feed, is_taipei_market_closure_event
FIX=Path(__file__).resolve().parents[1]/"fixtures/m8a_emergency_closure/taipei_closure_atom.xml"
def atom(summary,msg="Alert",updated="2026-07-10T00:00:00+08:00"):
    return f'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>x</id><updated>{updated}</updated><summary>{summary}</summary><msgType xmlns="urn:oasis:names:tc:emergency:cap:1.2">{msg}</msgType></entry></feed>'
def test_taipei_full_day_and_morning_closure():
    r=parse_closure_feed(FIX.read_text(),target_date="2026-07-10"); ev=r['events'][0]
    assert is_taipei_market_closure_event(ev,"2026-07-10")
    assert ev['expires_at'] and ev['closure_scope']=='full_day' and r['raw_xml_retained'] is False
    assert is_taipei_market_closure_event(parse_closure_feed(atom('臺北市 2026年7月10日 上午停止上班停止上課'))['events'][0],"2026-07-10")
def test_non_triggering_cases_and_cancel_update():
    cases=['臺北市信義區 2026年7月10日 停止上班','高雄市 2026年7月10日 停止上班','臺北市 2026年7月10日 晚上停止上班','臺北市 2026年7月10日 已達停止上班標準','臺北市 2026年7月10日 照常上班']
    for s in cases:
        assert not is_taipei_market_closure_event(parse_closure_feed(atom(s))['events'][0],"2026-07-10")
    ev=parse_closure_feed(atom('臺北市 2026年7月10日 全市停止上班','Cancel'))['events'][0]
    assert ev['decision_status']=='cancelled'
def test_target_date_filter_and_malformed_xml():
    assert parse_closure_feed(atom('臺北市 2026年7月9日 全市停止上班'), target_date='2026-07-10')['events']==[]
    assert parse_closure_feed('<bad')['parse_status']=='malformed_xml'
