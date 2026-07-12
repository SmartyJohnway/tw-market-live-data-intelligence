"""Bounded NCDR/DGPA work-closure Atom/CAP helper for M8A currentness."""
from __future__ import annotations
import re, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from scripts.m8a_official_eod_observation import utc_now
SOURCE_ID="NCDR_DGPA_CLOSURE_CAP"; URL="https://alerts.ncdr.nat.gov.tw/RssAtomFeed.ashx?AlertType=33"; SCHEMA_VERSION="m8a_emergency_work_closure_event.v1"
TAIPEI=ZoneInfo("Asia/Taipei")
def _txt(e): return "" if e is None or e.text is None else e.text.strip()
def _local(tag): return tag.split('}',1)[-1]
def _first(entry,name):
    for x in entry.iter():
        if _local(x.tag)==name: return _txt(x)
    return ""
def _updated_dt(updated:str):
    text=(updated or "").strip()
    if text.endswith("Z"): text=text[:-1]+"+00:00"
    try: dt=datetime.fromisoformat(text)
    except ValueError: return None
    if dt.tzinfo is None: dt=dt.replace(tzinfo=TAIPEI)
    return dt.astimezone(TAIPEI)
def _area(summary):
    head=summary.split(":",1)[0].split("：",1)[0]
    if "臺北市" in head or "台北市" in head or "臺北市" in summary or "台北市" in summary:
        level="local_area" if ("區" in head and "全市" not in summary) else "municipality"
        return "63","臺北市",level
    m=re.search(r"(新北市|桃園市|臺中市|台中市|臺南市|台南市|高雄市|基隆市|新竹市|嘉義市|新竹縣|苗栗縣|彰化縣|南投縣|雲林縣|嘉義縣|屏東縣|宜蘭縣|花蓮縣|臺東縣|台東縣|澎湖縣|金門縣|連江縣)",summary)
    return (None,m.group(1),"municipality") if m else (None,None,"unknown")
def _target_date(summary, updated):
    base=_updated_dt(updated)
    m=re.search(r"(20\d{2})[-/年](\d{1,2})[-/月](\d{1,2})",summary)
    if m: return f"{int(m.group(1)):04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    m=re.search(r"(\d{3})年(\d{1,2})月(\d{1,2})日",summary)
    if m: return f"{int(m.group(1))+1911:04d}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"
    if base:
        if re.search(r"今天|今日", summary): return base.date().isoformat()
        if re.search(r"明天|明日", summary): return (base.date()+timedelta(days=1)).isoformat()
        m=re.search(r"(?<!\d)(\d{1,2})\s*/\s*(\d{1,2})(?!\d)",summary)
        if not m: m=re.search(r"(?<!\d)(\d{1,2})月(\d{1,2})日",summary)
        if m:
            month=int(m.group(1)); day=int(m.group(2)); year=base.year
            return f"{year:04d}-{month:02d}-{day:02d}"
    return None
def _statuses(summary):
    closed=("停止上班" in summary or "停班" in summary) and "照常上班" not in summary
    school=("停止上課" in summary or "停課" in summary) and "照常上課" not in summary
    if "未達" in summary or "照常上班" in summary: decision="normal_operations"
    elif "已達" in summary or "達停止上班" in summary: decision="criteria_met"
    elif "尚未" in summary or "待宣布" in summary: decision="pending_announcement"
    elif closed: decision="closure_confirmed"
    else: decision="unknown"
    if "下午" in summary: scope="afternoon"
    elif "上午" in summary: scope="morning"
    elif "晚上" in summary or "晚間" in summary: scope="evening"
    elif "全日" in summary or "停止上班" in summary: scope="full_day"
    else: scope="unknown"
    if closed and decision == "criteria_met" and ("停止上班" in summary and "停止上課" in summary):
        decision="closure_confirmed"
    return ("closed" if closed else "open"),("closed" if school else "open"),decision,scope
def parse_closure_feed(xml_text:str, *, target_date:str|None=None):
    try: root=ET.fromstring(xml_text)
    except ET.ParseError:
        return {"schema_version":"m8a_emergency_work_closure_parse_result.v1","source_id":SOURCE_ID,"parse_status":"malformed_xml","events":[],"raw_xml_retained":False,"closure_query_succeeded":False,"caveats":["malformed XML"]}
    events=[]
    for entry in [e for e in root.iter() if _local(e.tag)=="entry"]:
        summary=_first(entry,"summary") or _first(entry,"title")
        updated=_first(entry,"updated"); entry_id=_first(entry,"id"); msg=_first(entry,"msgType") or ("Cancel" if "取消" in summary else ("Update" if "更新" in summary else "Alert")); status=_first(entry,"status") or "unknown"
        references=_first(entry,"references") or _first(entry,"supersedes")
        area_code,area_name,area_level=_area(summary); td=_target_date(summary,updated); work,school,decision,scope=_statuses(summary)
        if msg == "Cancel": decision="cancelled"
        caveats=[] if status == "Actual" else ["non-Actual CAP status is non-actionable for market closure"]
        ev={"schema_version":SCHEMA_VERSION,"source_id":SOURCE_ID,"entry_id":entry_id,"message_type":msg,"status":status,"references":references,"area_code":area_code,"area_name":area_name,"area_level":area_level,"target_date":td,"work_status":work,"school_status":school,"decision_status":decision,"closure_scope":scope,"published_at":updated,"effective_at":_first(entry,"effective"),"expires_at":_first(entry,"expires"),"source_cap_url":"","parse_status":"structured","caveats":caveats}
        if target_date is None or ev["target_date"]==target_date: events.append(ev)
    folded={}; rank={"Alert":1,"Update":2,"Cancel":3}
    def order(ev):
        dt=_updated_dt(ev.get("published_at") or "")
        return (dt.isoformat() if dt else "", 1 if ev.get("references") else 0, rank.get(ev.get("message_type"),0))
    for ev in events:
        key=(ev.get("target_date"),ev.get("area_code") or ev.get("area_name"),"work_school_closure")
        old=folded.get(key)
        if old is None or order(ev) >= order(old): folded[key]=ev
    return {"schema_version":"m8a_emergency_work_closure_parse_result.v1","source_id":SOURCE_ID,"parse_status":"ok","events":list(folded.values()),"raw_xml_retained":False,"closure_query_succeeded":True,"caveats":[]}
def fetch_closure_feed(*,timeout:int=10):
    req=urllib.request.Request(URL,method="GET",headers={"Accept":"application/atom+xml, application/xml","User-Agent":"tw-market-m8a-currentness/1.0"})
    with urllib.request.urlopen(req,timeout=timeout) as resp: return resp.read().decode("utf-8","replace"), resp.status, resp.headers.get("Content-Type","")
def fetch_and_parse_closure_feed(*,target_date:str|None=None,timeout:int=10):
    xml,status,ctype=fetch_closure_feed(timeout=timeout); r=parse_closure_feed(xml,target_date=target_date); r["provenance"]={"source_url":URL,"http_status":status,"content_type":ctype,"retrieved_at_utc":utc_now()}; return r
def is_taipei_market_closure_event(ev:dict,target_date:str)->bool:
    return ev.get("status")=="Actual" and ev.get("area_name")=="臺北市" and ev.get("area_level")=="municipality" and ev.get("work_status")=="closed" and ev.get("closure_scope") in {"full_day","morning"} and ev.get("decision_status")=="closure_confirmed" and ev.get("target_date")==target_date
