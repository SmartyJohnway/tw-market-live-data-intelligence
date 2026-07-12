from pathlib import Path
from scripts.m8a_ncdr_dgpa_closure_cap import parse_closure_feed, is_taipei_market_closure_event
FIX=Path(__file__).resolve().parents[1]/"fixtures/m8a_emergency_closure/taipei_closure_atom.xml"
REALISTIC=Path(__file__).resolve().parents[1]/"fixtures/m8a_emergency_closure/realistic_ncdr_atom.xml"
def atom(summary,msg="Alert",updated="2026-07-10T00:00:00+08:00",status="Actual",entry_id="x",references=""):
    refs=f'<references xmlns="urn:oasis:names:tc:emergency:cap:1.2">{references}</references>' if references else ""
    return f'<feed xmlns="http://www.w3.org/2005/Atom"><entry><id>{entry_id}</id><updated>{updated}</updated><summary>{summary}</summary><msgType xmlns="urn:oasis:names:tc:emergency:cap:1.2">{msg}</msgType><status xmlns="urn:oasis:names:tc:emergency:cap:1.2">{status}</status>{refs}</entry></feed>'
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


def test_realistic_ncdr_summary_7_10_and_yearless_updated_year():
    r=parse_closure_feed(REALISTIC.read_text(), target_date="2026-07-10")
    ev=[e for e in r['events'] if e['area_name']=='臺北市' and e['area_level']=='municipality' and e['closure_scope']=='full_day'][0]
    assert ev['target_date']=='2026-07-10'
    assert is_taipei_market_closure_event(ev, '2026-07-10')
    assert ev['closure_scope'] == 'full_day'

def test_today_tomorrow_use_entry_updated_timestamp_not_system_date():
    today=parse_closure_feed(atom('臺北市:今天下午1:00起停止上班', updated='2026-07-10T10:00:00+08:00'))['events'][0]
    tomorrow=parse_closure_feed(atom('臺北市:明天停止上班、停止上課', updated='2026-07-10T20:00:00+08:00'))['events'][0]
    assert today['target_date']=='2026-07-10' and today['closure_scope']=='afternoon'
    assert tomorrow['target_date']=='2026-07-11'

def test_older_full_day_alert_followed_by_newer_afternoon_update_wins():
    xml='''<feed xmlns="http://www.w3.org/2005/Atom">
    <entry><id>a1</id><updated>2026-07-09T18:00:00+08:00</updated><summary>臺北市:7/10停止上班、停止上課</summary><msgType xmlns="urn:oasis:names:tc:emergency:cap:1.2">Alert</msgType><status xmlns="urn:oasis:names:tc:emergency:cap:1.2">Actual</status></entry>
    <entry><id>a2</id><updated>2026-07-09T20:00:00+08:00</updated><summary>臺北市:7/10下午1:00起停止上班</summary><msgType xmlns="urn:oasis:names:tc:emergency:cap:1.2">Update</msgType><status xmlns="urn:oasis:names:tc:emergency:cap:1.2">Actual</status><references xmlns="urn:oasis:names:tc:emergency:cap:1.2">a1</references></entry>
    </feed>'''
    events=parse_closure_feed(xml,target_date='2026-07-10')['events']
    assert len([e for e in events if e['area_name']=='臺北市']) == 1
    assert events[0]['closure_scope']=='afternoon' and events[0]['entry_id']=='a2'
    assert events[0]['references']=='a1'
    assert not is_taipei_market_closure_event(events[0], '2026-07-10')


def test_older_full_day_alert_followed_by_newer_normal_operations_update_wins():
    xml='''<feed xmlns="http://www.w3.org/2005/Atom">
    <entry><id>n1</id><updated>2026-07-09T18:00:00+08:00</updated><summary>臺北市:7/10停止上班、停止上課</summary><msgType xmlns="urn:oasis:names:tc:emergency:cap:1.2">Alert</msgType><status xmlns="urn:oasis:names:tc:emergency:cap:1.2">Actual</status></entry>
    <entry><id>n2</id><updated>2026-07-09T21:00:00+08:00</updated><summary>臺北市:7/10照常上班、照常上課</summary><msgType xmlns="urn:oasis:names:tc:emergency:cap:1.2">Update</msgType><status xmlns="urn:oasis:names:tc:emergency:cap:1.2">Actual</status><references xmlns="urn:oasis:names:tc:emergency:cap:1.2">n1</references></entry>
    </feed>'''
    ev=parse_closure_feed(xml,target_date='2026-07-10')['events'][0]
    assert ev['entry_id']=='n2'
    assert ev['decision_status']=='normal_operations'
    assert ev['work_status']=='open'
    assert not is_taipei_market_closure_event(ev, '2026-07-10')


def test_older_afternoon_alert_followed_by_newer_full_day_update_wins():
    xml='''<feed xmlns="http://www.w3.org/2005/Atom">
    <entry><id>f1</id><updated>2026-07-09T18:00:00+08:00</updated><summary>臺北市:7/10下午1:00起停止上班</summary><msgType xmlns="urn:oasis:names:tc:emergency:cap:1.2">Alert</msgType><status xmlns="urn:oasis:names:tc:emergency:cap:1.2">Actual</status></entry>
    <entry><id>f2</id><updated>2026-07-09T20:00:00+08:00</updated><summary>臺北市:7/10停止上班、停止上課</summary><msgType xmlns="urn:oasis:names:tc:emergency:cap:1.2">Update</msgType><status xmlns="urn:oasis:names:tc:emergency:cap:1.2">Actual</status></entry>
    </feed>'''
    events=parse_closure_feed(xml,target_date='2026-07-10')['events']
    assert len([e for e in events if e['area_name']=='臺北市']) == 1
    assert events[0]['closure_scope']=='full_day' and events[0]['entry_id']=='f2'
    assert is_taipei_market_closure_event(events[0], '2026-07-10')

def test_cancel_supersedes_prior_closure_even_when_scope_changes():
    xml='''<feed xmlns="http://www.w3.org/2005/Atom">
    <entry><id>c1</id><updated>2026-07-09T18:00:00+08:00</updated><summary>臺北市:7/10停止上班、停止上課</summary><msgType xmlns="urn:oasis:names:tc:emergency:cap:1.2">Alert</msgType><status xmlns="urn:oasis:names:tc:emergency:cap:1.2">Actual</status></entry>
    <entry><id>c2</id><updated>2026-07-09T21:00:00+08:00</updated><summary>臺北市:7/10下午取消停止上班</summary><msgType xmlns="urn:oasis:names:tc:emergency:cap:1.2">Cancel</msgType><status xmlns="urn:oasis:names:tc:emergency:cap:1.2">Actual</status><references xmlns="urn:oasis:names:tc:emergency:cap:1.2">c1</references></entry>
    </feed>'''
    events=parse_closure_feed(xml,target_date='2026-07-10')['events']
    assert len(events)==1
    assert events[0]['decision_status']=='cancelled'


def test_cap_status_actual_required_for_taipei_market_closure_rule():
    test_ev=parse_closure_feed(atom('臺北市:7/10停止上班、停止上課', status='Test'), target_date='2026-07-10')['events'][0]
    actual_ev=parse_closure_feed(atom('臺北市:7/10停止上班、停止上課', status='Actual'), target_date='2026-07-10')['events'][0]
    assert test_ev['status']=='Test'
    assert test_ev['caveats']
    assert not is_taipei_market_closure_event(test_ev, '2026-07-10')
    assert is_taipei_market_closure_event(actual_ev, '2026-07-10')
