"""G1 normalization using only supplied official source payloads."""
from __future__ import annotations
import hashlib, json
from datetime import datetime
from typing import Any
from .research_executor import ROUTES, SourceFailure, bind_rows, failed_provenance, fetch_once, field, normalize_source_rows

SOURCE_FAMILY="MOPS_MATERIAL_DISCLOSURE_OPEN_DATA"

def _date(value: str | None) -> str | None:
    if not value: return None
    value=value.replace("/", "").replace("-", "").strip()
    if len(value)==7 and value.isdigit(): value=f"{int(value[:3])+1911:04d}-{value[3:5]}-{value[5:]}"
    elif len(value)==8 and value.isdigit(): value=f"{value[:4]}-{value[4:6]}-{value[6:]}"
    if len(value)!=10: return None
    try: return datetime.strptime(value,"%Y-%m-%d").date().isoformat()
    except ValueError: return None

def _published(row: dict[str, Any]) -> tuple[str | None, str | None]:
    date=_date(field(row,"publication_date","發言日期","日期","announcement_date")); raw=field(row,"publication_time","發言時間","時間","announcement_time")
    if not date or not raw: return None, raw
    digits=raw.zfill(6)
    if not digits.isdigit() or int(digits[:2])>23 or int(digits[2:4])>59 or int(digits[4:])>59: return None, raw
    return f"{date}T{digits[:2]}:{digits[2:4]}:{digits[4:]}+08:00", raw

def execute(targets: list[dict[str, Any]], market: str, *, observed_at: str, csv_fetcher, json_fetcher) -> list[dict[str, Any]]:
    route=ROUTES[("material_disclosures",market)]
    if any(target.get("market") != market for target in targets):
        return [_result(target,"binding_failed",[],observed_at,route,"official_csv",False,["route_target_market_mismatch"]) for target in targets]
    transport_result=None
    try:
        transport_result=fetch_once(route,csv_fetcher,json_fetcher)
        rows=normalize_source_rows(route,transport_result.transport,transport_result.rows)
        row_report_dates=[_date(field(row,"source_report_date")) for row in rows]
        if any(value is None for value in row_report_dates) or len(set(row_report_dates))!=1:
            raise SourceFailure("source_snapshot_report_date_invalid")
    except SourceFailure as exc:
        transport, fallback_used, fallback_attempted, attempts=failed_provenance(transport_result,exc)
        return [_result(t,"source_failed",[],observed_at,route,transport,fallback_used,[exc.code],
                        diagnostics=[], source_report_date=None, attempts=attempts,
                        fallback_attempted=fallback_attempted) for t in targets]
    transport=transport_result.transport; fallback=transport_result.fallback_attempted; attempts=transport_result.attempt_failures
    source_report_date=row_report_dates[0]
    out=[]
    for target in targets:
        status, matches, diagnostics=bind_rows(rows,target)
        if status=="binding_failed":
            out.append(_result(target,status,[],observed_at,route,transport,fallback,["exact_company_code_binding_failed"],
                               diagnostics=_binding_diagnostics(diagnostics), source_report_date=source_report_date,
                               attempts=attempts)); continue
        items=[]
        for row in matches:
            published, raw_time=_published(row)
            if not published:
                failure_attempts=attempts + [{"transport":transport,"failure":"required_publication_time_invalid"}]
                out.append(_result(target,"source_failed",[],observed_at,route,transport,False,["required_publication_time_invalid"],
                                   diagnostics=[], source_report_date=source_report_date, attempts=failure_attempts,
                                   fallback_attempted=transport_result.fallback_attempted)); break
            raw=json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(",",":")); h=hashlib.sha256(raw.encode()).hexdigest()
            items.append({"normalized_record_hash":h,"published_at":published,"source_fact_date":_date(field(row,"事實發生日","source_fact_date")),"raw_speech_time":raw_time,"subject":field(row,"主旨","subject") or "","clause":field(row,"符合條款","clause"),"description_raw":field(row,"說明","description") or "","revision_relation":{"status":"unresolved","relation_type":None,"related_official_reference":None}})
        else:
            identities={}
            for item in items:
                identity=(item["published_at"], item["subject"], item["clause"])
                identities.setdefault(identity, set()).add(item["normalized_record_hash"])
            if any(len(hashes)>1 for hashes in identities.values()):
                out.append(_result(target,"binding_failed",[],observed_at,route,transport,fallback,["conflicting_duplicate_normalized_source_rows"],
                                   diagnostics=[_conflict_diagnostic(items)], source_report_date=source_report_date,
                                   attempts=attempts)); continue
            items.sort(key=lambda x: x["normalized_record_hash"])
            items.sort(key=lambda x: x["published_at"], reverse=True)
            truncated=len(items)>50; items=items[:50]
            out.append(_result(target,"partial" if truncated else ("available" if items else "no_evidence_in_covered_scope"),items,observed_at,route,transport,fallback,[],
                               diagnostics=_binding_diagnostics(diagnostics), source_report_date=source_report_date,
                               attempts=attempts));
    return out

def _binding_diagnostics(rows):
    return [] if not rows else [{"kind":"company_name_mismatch","source_company_codes":sorted({str(x.get("company_code", "")) for x in rows})}]
def _conflict_diagnostic(items):
    return {"kind":"binding_conflict","normalized_record_hashes":sorted(x["normalized_record_hash"] for x in items)}
def _result(target,status,items,observed_at,route,transport,fallback,caveats,diagnostics=None,source_report_date=None,attempts=None,fallback_attempted=None):
    attempted=fallback if fallback_attempted is None else fallback_attempted
    return {"schema_version":"phase_g_material_disclosure_operation_evidence.v1","executor_id":"phase_g_official_research_executor","capability_id":"material_disclosures","target":{k:target[k] for k in ("canonical_target_id","market","security_code")},"status":status,"source":{"source_family":SOURCE_FAMILY,"source_contract_id":route["contract"],"transport":transport,"fallback_used":fallback,"fallback_attempted":attempted,"attempt_failures":attempts or []},"observed_at":observed_at,"coverage":{"mode":"latest_completed_official_daily_batch","source_report_date":source_report_date,"coverage_through":max((x["published_at"][:10] for x in items),default=None),"truncated":status=="partial"},"items":items,"diagnostics":diagnostics or [],"caveats":caveats}
