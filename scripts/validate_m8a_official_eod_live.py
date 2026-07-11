#!/usr/bin/env python3
"""Manual bounded live validation for M8A official EOD adapters."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from datetime import datetime
from zoneinfo import ZoneInfo
from scripts.m8a_official_eod_execution import execute_official_eod_refresh
from scripts.m8a_ncdr_dgpa_closure_cap import fetch_and_parse_closure_feed

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--sources', required=True, help='Comma-separated TWSE_OPENAPI,TPEX_OPENAPI')
    ap.add_argument('--symbols', required=True, help='Comma-separated symbols')
    ap.add_argument('--confirm', action='store_true')
    ap.add_argument('--timeout', type=int, default=20)
    args=ap.parse_args()
    sources=[s.strip() for s in args.sources.split(',') if s.strip()]
    symbols=[s.strip() for s in args.symbols.split(',') if s.strip()]
    eval_time = datetime.now(ZoneInfo("Asia/Taipei")).replace(microsecond=0).isoformat()
    def closure_fetcher(target_date):
        return fetch_and_parse_closure_feed(target_date=target_date, timeout=args.timeout)
    result=execute_official_eod_refresh(symbols,sources,args.confirm, closure_fetcher=closure_fetcher, evaluation_time_asia_taipei=eval_time)
    compact={
      'schema_version': result['schema_version'], 'overall_status': result['overall_status'],
      'requested_sources': result['requested_sources'], 'requested_symbols': result['requested_symbols'],
      'source_statuses': [{'source_id': r.get('source_id'), 'batch_status': r.get('batch_status'), 'reported_trade_dates': r.get('reported_trade_dates'), 'row_count_retained': r.get('row_count_retained')} for r in result.get('source_results',[])],
      'calendar_resolution': result.get('calendar_resolution'),
      'retained_observations': [{'source_id': o.get('source_id'), 'market': o.get('market'), 'symbol': o.get('symbol'), 'trade_date': o.get('trade_date'), 'observation_status': o.get('observation_status'), 'instrument_type': o.get('instrument_type')} for o in result.get('normalized_observations',[])]
    }
    print(json.dumps(compact, ensure_ascii=False, indent=2))
if __name__ == '__main__': main()
