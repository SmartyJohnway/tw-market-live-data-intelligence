"""Bounded NCDR/DGPA work-closure Atom/CAP helper for M8A currentness."""
from __future__ import annotations
import re, urllib.request, xml.etree.ElementTree as ET
from scripts.m8a_official_eod_observation import utc_now
SOURCE_ID="NCDR_DGPA_CLOSURE_CAP"; URL="https://alerts.ncdr.nat.gov.tw/RssAtomFeed.ashx?AlertType=33"; SCHEMA_VERSION="m8a_emergency_work_closure_event.v1"
def _txt(e): return "" if e is None or e.text is None else e.text.strip()
def _local(tag): return tag.split('}',1)[-1]
def _first(entry,name):
    for x in entry.iter():
        if _local(x.tag)==name: return _txt(x)
    return ""
def _area(summary):
    if "臺北市" in summary or "台北市" in summary: return "63","臺北市","municipality"
    m=re.search(r"(新北市|桃園市|臺中市|台中市|臺南市|台南市|高雄市|基隆市|新竹市|嘉義市|新竹縣|苗栗縣|彰化縣|南投縣|雲林縣|嘉義縣|屏東縣|宜蘭縣|花蓮縣|臺東縣|台東縣|澎湖縣|金門縣|連江縣)",summary)
    return (None,m.group(1),"municipality") if m else (None,None,"unknown")
def _target_date(summary, updated):
    m=re.search(r"(20\d{2})[-/年](\d{1,2})[-/月](\d{1,2})",summary)
    if m: return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m=re.search(r"(\d{3})年(\d{1,2})月(\d{1,2})日",summary)
    if m: return f"{int(m.group(1))+1911:04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    return None
def _statuses(summary):
    closed=("停止上班" in summary or "停班" in summary) and "照常上班" not in summary
    school=("停止上課" in summary or "停課" in summary) and "照常上課" not in summary
    if "未達" in summary: decision="normal_operations"
    elif "達停止上班" in summary and "宣布" not in summary: decision="criteria_met"
    elif "尚未" in summary or "待宣布" in summary: decision="pending_announcement"
    elif closed: decision="closure_confirmed"
    else: decision="unknown"
    if "上午" in summary: scope="morning"
    elif "晚上" in summary or "晚間" in summary: scope="evening"
    elif "下午" in summary: scope="afternoon"
    elif "全日" in summary or "停止上班" in summary: scope="full_day"
    else: scope="unknown"
    if "區" in summary and "全市" not in summary: level="local_area"
    else: level=None
    return ("closed" if closed else "open"),("closed" if school else "open"),decision,scope,level
def parse_closure_feed(xml_text:str, *, target_date:str|None=None):
    try: root=ET.fromstring(xml_text)
    except ET.ParseError:
        return {"schema_version":"m8a_emergency_work_closure_parse_result.v1","source_id":SOURCE_ID,"parse_status":"malformed_xml","events":[],"raw_xml_retained":False,"caveats":["malformed XML"]}
    events=[]
    for entry in [e for e in root.iter() if _local(e.tag)=="entry"]:
        summary=_first(entry,"summary") or _first(entry,"title")
        updated=_first(entry,"updated"); entry_id=_first(entry,"id"); msg=_first(entry,"msgType") or ("Cancel" if "取消" in summary else ("Update" if "更新" in summary else "Alert")); status=_first(entry,"status") or "Actual"
        area_code,area_name,area_level=_area(summary); td=_target_date(summary,updated); work,school,decision,scope,level_override=_statuses(summary)
        if level_override: area_level=level_override
        if msg == "Cancel": decision="cancelled"
        ev={"schema_version":SCHEMA_VERSION,"source_id":SOURCE_ID,"entry_id":entry_id,"message_type":msg,"status":status,"area_code":area_code,"area_name":area_name,"area_level":area_level,"target_date":td,"work_status":work,"school_status":school,"decision_status":decision,"closure_scope":scope,"published_at":updated,"effective_at":_first(entry,"effective"),"expires_at":_first(entry,"expires"),"source_cap_url":"","parse_status":"structured","caveats":[]}
        if target_date is None or ev["target_date"]==target_date: events.append(ev)
    folded={}
    rank={"Alert":1,"Update":2,"Cancel":3}
    for ev in events:
        key=(ev.get("target_date"),ev.get("area_code") or ev.get("area_name"),ev.get("closure_scope"))
        old=folded.get(key)
        if old is None or (ev.get("published_at") or "",rank.get(ev.get("message_type"),0)) >= (old.get("published_at") or "",rank.get(old.get("message_type"),0)): folded[key]=ev
    return {"schema_version":"m8a_emergency_work_closure_parse_result.v1","source_id":SOURCE_ID,"parse_status":"ok","events":list(folded.values()),"raw_xml_retained":False,"caveats":[]}
def fetch_closure_feed(*,timeout:int=10):
    req=urllib.request.Request(URL,method="GET",headers={"Accept":"application/atom+xml, application/xml","User-Agent":"tw-market-m8a-currentness/1.0"})
    with urllib.request.urlopen(req,timeout=timeout) as resp: return resp.read().decode("utf-8","replace"), resp.status, resp.headers.get("Content-Type","")
def fetch_and_parse_closure_feed(*,target_date:str|None=None,timeout:int=10):
    xml,status,ctype=fetch_closure_feed(timeout=timeout); r=parse_closure_feed(xml,target_date=target_date); r["provenance"]={"source_url":URL,"http_status":status,"content_type":ctype,"retrieved_at_utc":utc_now()}; return r
def is_taipei_market_closure_event(ev:dict,target_date:str)->bool:
    return ev.get("area_name")=="臺北市" and ev.get("area_level")=="municipality" and ev.get("work_status")=="closed" and ev.get("closure_scope") in {"full_day","morning"} and ev.get("decision_status")=="closure_confirmed" and ev.get("target_date")==target_date
