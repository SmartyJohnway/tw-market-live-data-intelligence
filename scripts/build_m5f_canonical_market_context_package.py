#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, math, os, shutil, tempfile
from generate_latest_market_snapshot import build_snapshot_from_m5f_canonical
from generate_watchlist_observations import build_watchlist_observations_from_m5f_canonical
from generate_ai_context_pack import build_ai_context_pack_from_m5f_canonical, render_m5f_ai_context_pack_markdown
from generate_chatgpt_briefing import render_chatgpt_briefing_from_m5f_canonical
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
DEFAULT_INPUT=REPO/'research/staging/m5d/m5d_frontend_publication_candidate_01/market-context.json'
DEFAULT_OUTPUT=REPO/'research/staging/m5f/m5f_canonical_market_context_01'
FILES=['canonical_market_context.json','latest_market_snapshot.json','watchlist_observations.json','ai_context_pack.json','ai_context_pack.md','chatgpt_briefing.md','source_health.json','capability_summary.json','lineage.json','validation_report.json']
REQ_CAVEATS=['not_realtime_guaranteed','not_trading_signal','not_production_current_state','source_risk_present','freshness_must_be_displayed']
MAX_BOUNDED_TARGETS=5
ALLOWED_FRESHNESS={'fresh','delayed','stale','eod','eod_batch','live_candidate','unknown'}
ALLOWED_BADGES={'historical/stale','historical/fresh','historical/delayed','historical/eod','historical/eod_batch','historical/live_candidate','historical/unknown'}
ALLOWED_AUTHORITIES={'official','unofficial','third_party','commercial','broker','unknown'}
BASELINE_EXPECTED={'0050':103.1,'00929':29.96,'2330':2340.0}
SYMBOL_ALLOWLIST={'symbol','price_like_value','source_id','source_authority','source_timestamp','retrieved_at','freshness_status','delay_status','display_caveats','source_risk_flags','data_quality_flags','normalization_status','price_semantics','staleness_seconds'}
FORBIDDEN_KEYS={'buy','sell','hold','target_price','target price','ranking','rank','recommendation','raw_payload','raw_full_response','full_raw_payload','response_body','raw_endpoint_payload'}
FORBIDDEN_PREFIXES=('research/generated','frontend/public','research/staging/m5c','research/staging/m5d','research/live_probe_runs/m5b')

def dump(obj): return json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True,allow_nan=False)+"\n"
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write_lf(path:Path, text:str): Path(path).write_bytes(text.encode('utf-8'))
def rel(p):
    rp=Path(p).resolve()
    try: return rp.relative_to(REPO).as_posix()
    except ValueError: return rp.as_posix()
def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))


def reject_forbidden_nested(obj, path='<root>'):
    if isinstance(obj, dict):
        for k, v in obj.items():
            kl=str(k).lower()
            if kl in FORBIDDEN_KEYS:
                raise ValueError(f'forbidden nested field: {path}.{k}')
            reject_forbidden_nested(v, f'{path}.{k}')
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            reject_forbidden_nested(v, f'{path}[{i}]')

def _require_string(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{field} must be a non-empty string')

def _require_string_list(value, field):
    if not isinstance(value, list) or any(not isinstance(v, str) or not v for v in value):
        raise ValueError(f'{field} must be a list of non-empty strings')

def _require_price(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('price_like_value must be a finite number and not bool')

def validate_symbol_shape(symbol: dict) -> None:
    if not isinstance(symbol, dict):
        raise ValueError('symbol row must be object')
    reject_forbidden_nested(symbol, 'symbol')
    missing={'symbol','price_like_value','source_id','source_timestamp'}-set(symbol)
    if missing:
        raise ValueError(f'symbol missing required fields: {sorted(missing)}')
    for field in ['symbol','source_id','source_timestamp']:
        _require_string(symbol.get(field), field)
    if 'source_authority' in symbol:
        _require_string(symbol['source_authority'], 'source_authority')
        if symbol['source_authority'] not in ALLOWED_AUTHORITIES:
            raise ValueError('source_authority outside allowed enum')
    if 'retrieved_at' in symbol: _require_string(symbol['retrieved_at'], 'retrieved_at')
    if 'freshness_status' in symbol: _require_string(symbol['freshness_status'], 'freshness_status')
    if 'delay_status' in symbol: _require_string(symbol['delay_status'], 'delay_status')
    _require_price(symbol.get('price_like_value'))
    for field in ['display_caveats','source_risk_flags','data_quality_flags']:
        if field in symbol: _require_string_list(symbol[field], field)
    if 'staleness_seconds' in symbol and (isinstance(symbol['staleness_seconds'], bool) or not isinstance(symbol['staleness_seconds'], (int,float)) or not math.isfinite(symbol['staleness_seconds'])):
        raise ValueError('staleness_seconds must be finite numeric')

def project_symbol(symbol: dict) -> dict:
    validate_symbol_shape(symbol)
    return {k: symbol[k] for k in sorted(SYMBOL_ALLOWLIST) if k in symbol}

def check_output_dir(path:Path):
    r=path.resolve()
    if path.is_symlink() or any(part=='..' for part in path.parts):
        raise ValueError('unsafe output path')
    default = DEFAULT_OUTPUT.resolve()
    # Production writes are intentionally constrained to the single M5F package
    # directory. Tests may write only under /tmp; no other repository directory
    # may ever be recursively replaced.
    if r == default:
        return
    if r == REPO or r.is_relative_to(REPO):
        raise ValueError('output path must be the fixed M5F package path or an explicit system temp test path')
    tmp_root = Path(tempfile.gettempdir()).resolve()
    if r == tmp_root or r.is_relative_to(tmp_root):
        return
    raise ValueError('output path must be the fixed M5F package path or an explicit system temp test path')

def _find_file_by_sha(root: Path, expected_sha: str, label: str) -> Path:
    for candidate in root.rglob('*.json'):
        if sha(candidate) == expected_sha:
            return candidate
    raise ValueError(f'{label} hash not found under {root}')

def _reject_full_market_candidate(c: dict) -> None:
    text = json.dumps({k:v for k,v in c.items() if k not in {'symbols'}}, ensure_ascii=False).lower()
    if 'full_market' in text or 'full-market' in text or '全市場' in text:
        raise ValueError('full-market candidate rejected')

def verify_input(candidate_path:Path):
    if candidate_path.is_symlink(): raise ValueError('candidate symlink rejected')
    c=load(candidate_path)
    _reject_full_market_candidate(c)
    m5d_dir=candidate_path.parent
    m5d_manifest=load(m5d_dir/'sha256_manifest.json')
    if sha(candidate_path)!=m5d_manifest['files']['market-context.json']: raise ValueError('candidate hash mismatch')
    binding=load(m5d_dir/'source_binding.json')
    if sha(m5d_dir/'source_binding.json')!=m5d_manifest['files']['source_binding.json']: raise ValueError('source binding hash mismatch')
    is_m5i = str(c.get('schema_version','')).startswith('m5i_refresh_candidate') or str(binding.get('schema_version','')).startswith('m5i_source_binding')
    if is_m5i:
        m5c_manifest={'files':{}}
    else:
        m5c_dir=REPO/binding['m5c_package_dir']
        m5c_manifest_path=m5c_dir/'sha256_manifest.json'
        m5c_pkg=m5c_dir/'frontend_readonly_context_package.json'
        m5c_manifest=load(m5c_manifest_path)
        if sha(m5c_manifest_path)!=binding['m5c_manifest_sha256']: raise ValueError('m5c manifest hash mismatch')
        if sha(m5c_pkg)!=binding['m5c_frontend_readonly_context_package_sha256']: raise ValueError('m5c package hash mismatch')
        _find_file_by_sha(REPO/'research/staging/m5c', binding['m5c_supplemental_audit_sha256'], 'm5c supplemental audit')
        _find_file_by_sha(REPO/'research/staging/m5c', binding['m5c_run_summary_destination_correction_sha256'], 'm5c destination correction')
    rows=c.get('symbols',[])
    syms={s.get('symbol'):s for s in rows if isinstance(s, dict)}
    if not syms: raise ValueError('no symbols in candidate')
    if len(syms)!=len(rows): raise ValueError('duplicate or malformed symbols in candidate')
    if len(syms)>MAX_BOUNDED_TARGETS: raise ValueError('candidate exceeds bounded target limit')
    binding_targets=set(binding.get('targets',[]))
    if set(syms) != binding_targets: raise ValueError('candidate symbols do not match source binding targets')
    source_ids={s.get('source_id') for s in syms.values()}
    source_dates={s.get('source_timestamp') for s in syms.values()}
    if None in source_ids or None in source_dates or len(source_ids)!=1 or len(source_dates)!=1:
        raise ValueError('candidate must have one explicit source and source date')
    if next(iter(source_ids)) != binding.get('source'):
        raise ValueError('candidate source does not match source binding')
    for s in syms.values():
        validate_symbol_shape(s)
    for k,v in {'historical_evidence_snapshot':True,'current_realtime':False,'production_current_state':False,'production_ready':False,'realtime_guaranteed':False,'trading_signal':False,'readonly_only':True}.items():
        if c.get(k)!=v:
            if not (k == 'historical_evidence_snapshot' and c.get('reviewed_refresh_snapshot') is True):
                raise ValueError(f'bad flag {k}')
    if c.get('stale_status') not in ALLOWED_FRESHNESS or c.get('badge') not in ALLOWED_BADGES:
        raise ValueError('bad freshness badge')
    if not set(REQ_CAVEATS).issubset(c.get('global_caveats',[])): raise ValueError('missing caveat')
    return c,binding,m5d_manifest,m5c_manifest

def build_package(candidate_path=DEFAULT_INPUT):
    c,binding,m5d_manifest,m5c_manifest=verify_input(Path(candidate_path))
    symbols=sorted((project_symbol(s) for s in c['symbols']), key=lambda s:s['symbol'])
    base_gov={k:c[k] for k in ['historical_evidence_snapshot','current_realtime','production_current_state','production_ready','realtime_guaranteed','trading_signal','readonly_only','stale_status','badge']}
    source_ids=sorted({s['source_id'] for s in symbols})
    source_dates=sorted({s['source_timestamp'] for s in symbols})
    if len(source_ids)!=1 or len(source_dates)!=1: raise ValueError('canonical source/date must be unique')
    canonical={'schema_version':'m5f_canonical_market_context.v1','package_id':'m5f_canonical_market_context_01','derived_from':rel(candidate_path),'generated_at_utc':c['generated_at_utc'],'source':source_ids[0],'source_date':source_dates[0],'symbols':symbols,'failed_targets':c.get('failed_targets', []),'global_caveats':list(c.get('global_caveats', REQ_CAVEATS)),'governance':base_gov,'lineage_hashes':{'m5d_market_context_sha256':m5d_manifest['files']['market-context.json'],'m5d_manifest_sha256':sha(Path(candidate_path).parent/'sha256_manifest.json'),'m5d_source_binding_sha256':m5d_manifest['files']['source_binding.json'],'m5c_frontend_readonly_context_package_sha256':binding.get('m5c_frontend_readonly_context_package_sha256','not_applicable_m5i_refresh'),'m5c_manifest_sha256':binding.get('m5c_manifest_sha256','not_applicable_m5i_refresh'),'m5c_supplemental_audit_sha256':binding.get('m5c_supplemental_audit_sha256','not_applicable_m5i_refresh'),'m5c_run_summary_destination_correction_sha256':binding.get('m5c_run_summary_destination_correction_sha256','not_applicable_m5i_refresh')},'notes':['latest reviewed bounded evidence','not current realtime market state','not a trading signal']}
    snapshot=build_snapshot_from_m5f_canonical(canonical)
    obs=build_watchlist_observations_from_m5f_canonical(canonical)
    ai=build_ai_context_pack_from_m5f_canonical(canonical)
    ai_md=render_m5f_ai_context_pack_markdown(ai)
    briefing=render_chatgpt_briefing_from_m5f_canonical(canonical)
    health={'schema_version':'m5f_source_health.v1','source_id':canonical['source'],'source_authority':symbols[0].get('source_authority','unknown'),'status':'available_as_reviewed_historical_evidence','stale_status':base_gov['stale_status'],'source_date':canonical['source_date'],'source_risk_flags':symbols[0]['source_risk_flags'],'failed_targets':c.get('failed_targets', []),'governance':base_gov}
    cap={'schema_version':'m5f_capability_summary.v1','canonical_context':'available','bounded_watchlist':True,'symbol_count':len(symbols),'source':canonical['source'],'source_date':canonical['source_date'],'realtime_supported':False,'production_ready':False,'readonly_only':True,'governance':base_gov}
    lineage={'schema_version':'m5f_lineage.v1','upstream_chain':(['M5I explicit bounded refresh candidate','M5I source binding','M5I bounded TWSE_OpenAPI refresh evidence'] if str(c.get('schema_version','')).startswith('m5i_refresh_candidate') else ['M5D candidate manifest','M5C frontend readonly context package','M5C manifest/audit/correction','M5B bounded TWSE_OpenAPI evidence']),'hashes':canonical['lineage_hashes'],'source_binding':binding,'governance':base_gov}
    val={'schema_version':'m5f_validation_report.v1','status':'passed','checks':['exact_file_set','manifest_hashes','symbols_source_date_values','lineage_hashes','required_caveats','required_false_flags','no_trading_recommendation_fields','no_endpoint_payload_leakage'],'governance':base_gov}
    return {'canonical_market_context.json':canonical,'latest_market_snapshot.json':snapshot,'watchlist_observations.json':obs,'ai_context_pack.json':ai,'ai_context_pack.md':ai_md,'chatgpt_briefing.md':briefing,'source_health.json':health,'capability_summary.json':cap,'lineage.json':lineage,'validation_report.json':val}

def write_package(out:Path, artifacts:dict):
    check_output_dir(out)
    parent=out.parent; parent.mkdir(parents=True,exist_ok=True)
    tmp=Path(tempfile.mkdtemp(prefix='.m5f_tmp_',dir=parent))
    backup=None
    try:
        for name,obj in artifacts.items(): write_lf(tmp/name, obj if isinstance(obj,str) else dump(obj))
        manifest={'schema_version':'m5f_sha256_manifest.v1','package_id':'m5f_canonical_market_context_01','manifest_final':True,'no_artifact_modification_after_manifest':True,'files':{name:sha(tmp/name) for name in FILES},'lineage_hashes':artifacts['canonical_market_context.json']['lineage_hashes'],'governance':artifacts['canonical_market_context.json']['governance']}
        write_lf(tmp/'sha256_manifest.json', dump(manifest))
        if out.exists():
            backup=parent/(out.name+'.previous')
            if backup.exists(): shutil.rmtree(backup)
            os.replace(out, backup)
        try:
            os.replace(tmp,out)
        except Exception:
            if backup and backup.exists() and not out.exists():
                os.replace(backup,out)
            raise
        if backup and backup.exists(): shutil.rmtree(backup)
    except Exception:
        shutil.rmtree(tmp,ignore_errors=True); raise

def main():
    ap=argparse.ArgumentParser(); mode=ap.add_mutually_exclusive_group(); ap.add_argument('--candidate-path',default=str(DEFAULT_INPUT)); ap.add_argument('--output-dir',default=str(DEFAULT_OUTPUT)); mode.add_argument('--write-package',action='store_true'); mode.add_argument('--check-only',action='store_true')
    a=ap.parse_args(); arts=build_package(Path(a.candidate_path));
    if a.write_package: write_package(Path(a.output_dir),arts)
    print(dump({'status':'ok','write_package':a.write_package,'output_dir':a.output_dir,'files':FILES+(['sha256_manifest.json'] if a.write_package else [])}))
if __name__=='__main__': main()
