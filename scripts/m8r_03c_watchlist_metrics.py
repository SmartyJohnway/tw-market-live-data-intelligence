from __future__ import annotations
import math, statistics
from typing import Any
from scripts.m8r_03c_conversation_contract_validator import M8R03CValidationError

METRIC_ORDER=("return_1d","return_5d","return_10d","return_20d","range_high","range_low","range_position","drawdown_from_recent_high","average_volume","volume_ratio","realized_volatility","relative_return_vs_market")
FORMULAS={
 'return_Nd':'latest_valid_close / close_N_trading_rows_ago - 1; unadjusted close unless source says otherwise',
 'range_high':'max(valid high/close over input rows)', 'range_low':'min(valid low/close over input rows)',
 'range_position':'(latest_close - range_low) / (range_high - range_low)',
 'drawdown_from_recent_high':'latest_close / range_high - 1', 'average_volume':'mean(valid volume over input period)',
 'volume_ratio':'latest_volume / average_volume_prior_window', 'realized_volatility':'sample standard deviation of daily log returns',
 'relative_return_vs_market':'target return_Nd - supplied benchmark return_Nd',
}

def _num(v):
    if v in (None,''): return None
    try: return float(v)
    except Exception: return None

def metric_record(metric_id, value, status, as_of, deps, period, formula_id=None, unit='ratio'):
    return {'metric_id':metric_id,'value': None if value is None else round(float(value), 8),'unit':unit,'formula_id':formula_id or metric_id,'input_period':period,'source_dependencies':deps,'calculation_status':status,'as_of':as_of}

def calculate_metrics(rows: list[dict[str, Any]], *, target_id: str, as_of: str, period: dict[str, Any], benchmark_rows: list[dict[str, Any]] | None=None) -> list[dict[str, Any]]:
    rows=sorted(rows, key=lambda r: r['trade_date'])
    closes=[_num(r.get('facts',{}).get('close') or r.get('facts',{}).get('latest_price')) for r in rows]
    highs=[_num(r.get('facts',{}).get('high') or r.get('facts',{}).get('close')) for r in rows]
    lows=[_num(r.get('facts',{}).get('low') or r.get('facts',{}).get('close')) for r in rows]
    vols=[_num(r.get('facts',{}).get('volume')) for r in rows]
    deps=[{'target_id':target_id,'source_family':r.get('source_family'),'trade_date':r.get('trade_date')} for r in rows]
    latest=closes[-1] if closes else None; out=[]
    for n in (1,5,10,20):
        if len(closes)>n and latest is not None and closes[-1-n] not in (None,0): status='calculated'; val=latest/closes[-1-n]-1
        else: status='input_unavailable'; val=None
        out.append(metric_record(f'return_{n}d',val,status,as_of,deps,period,'return_Nd'))
    valid_high=[x for x in highs if x is not None]; valid_low=[x for x in lows if x is not None]
    hi=max(valid_high) if valid_high else None; lo=min(valid_low) if valid_low else None
    out.append(metric_record('range_high',hi,'calculated' if hi is not None else 'input_unavailable',as_of,deps,period,'range_high','price'))
    out.append(metric_record('range_low',lo,'calculated' if lo is not None else 'input_unavailable',as_of,deps,period,'range_low','price'))
    out.append(metric_record('range_position', (latest-lo)/(hi-lo) if latest is not None and hi is not None and lo is not None and hi!=lo else None, 'calculated' if latest is not None and hi is not None and lo is not None and hi!=lo else 'input_unavailable', as_of,deps,period,'range_position'))
    out.append(metric_record('drawdown_from_recent_high', latest/hi-1 if latest is not None and hi else None, 'calculated' if latest is not None and hi else 'input_unavailable', as_of,deps,period,'drawdown_from_recent_high'))
    vv=[v for v in vols if v is not None]
    avg=sum(vv)/len(vv) if vv else None
    out.append(metric_record('average_volume',avg,'calculated' if avg is not None else 'input_unavailable',as_of,deps,period,'average_volume','shares'))
    prior=[v for v in vols[:-1] if v is not None]; pavg=sum(prior)/len(prior) if prior else None
    out.append(metric_record('volume_ratio', vols[-1]/pavg if vols and vols[-1] is not None and pavg else None, 'calculated' if vols and vols[-1] is not None and pavg else 'input_unavailable', as_of,deps,period,'volume_ratio'))
    rets=[math.log(closes[i]/closes[i-1]) for i in range(1,len(closes)) if closes[i] and closes[i-1]]
    out.append(metric_record('realized_volatility', statistics.stdev(rets) if len(rets)>=2 else None, 'calculated' if len(rets)>=2 else 'input_unavailable', as_of,deps,period,'realized_volatility'))
    if benchmark_rows:
        b=calculate_metrics(benchmark_rows, target_id='BENCHMARK', as_of=as_of, period=period, benchmark_rows=None)[0]
        t=out[0]
        val=t['value']-b['value'] if t['value'] is not None and b['value'] is not None else None
        status='calculated' if val is not None else 'input_unavailable'
    else: val=None; status='formula_not_applicable'
    out.append(metric_record('relative_return_vs_market',val,status,as_of,deps,period,'relative_return_vs_market'))
    return out
