from __future__ import annotations
import argparse, json, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8b_taifex_openapi_execution import execute_taifex_openapi_refresh


def _csv(value: str) -> list[str]:
    return [x for x in (value or '').split(',') if x]


def _selector_objects(args) -> list[dict]:
    if args.contracts_json:
        try:
            data = json.loads(args.contracts_json)
        except json.JSONDecodeError as exc:
            raise SystemExit(f'--contracts-json must be valid JSON: {exc}')
        if not isinstance(data, list) or not all(isinstance(x, dict) for x in data):
            raise SystemExit('--contracts-json must be a JSON array of objects')
        return data
    contracts=[]
    for item in filter(None, args.contracts.split(',')):
        parts=item.split(':'); d={}
        if len(parts)>0 and parts[0]: d['contract_month']=parts[0]
        if len(parts)>1 and parts[1]: d['strike_price']=parts[1]
        if len(parts)>2 and parts[2]: d['option_type']=parts[2]
        contracts.append(d)
    values={
        'contract_month': args.contract_month,
        'contract_month_or_week': args.contract_month,
        'strike_price': args.strike,
        'option_type': args.option_type,
        'delivery_month': args.delivery_month,
        'settlement_month': args.settlement_month,
        'type_of_traders': args.trader_type,
    }
    for key, vals in values.items():
        for val in vals or []:
            contracts.append({key: val})
    return contracts


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--contexts',required=True)
    p.add_argument('--products',default='')
    p.add_argument('--contracts',default='', help='legacy comma-separated contract[:strike[:option_type]] selectors')
    p.add_argument('--contracts-json', help='JSON array of selector objects')
    p.add_argument('--contract-month', action='append')
    p.add_argument('--strike', action='append')
    p.add_argument('--option-type', action='append')
    p.add_argument('--delivery-month', action='append')
    p.add_argument('--settlement-month', action='append')
    p.add_argument('--trader-type', action='append')
    p.add_argument('--trade-date', action='append')
    p.add_argument('--pcr-latest-n', type=int, default=1)
    p.add_argument('--max-pcr-rows', type=int, default=20)
    p.add_argument('--final-settlement-latest-n', type=int, default=1)
    p.add_argument('--max-final-settlement-rows', type=int, default=50)
    p.add_argument('--max-block-trade-rows', type=int, default=100)
    p.add_argument('--max-large-trader-oi-rows', type=int, default=100)
    p.add_argument('--session',action='append',dest='sessions')
    p.add_argument('--confirm',action='store_true')
    a=p.parse_args()
    contracts=_selector_objects(a)
    fixture_fetchers = None
    if os.environ.get("M8B_VALIDATOR_TEST_FIXTURE") == "1":
        fixture_fetchers = {name: (lambda endpoint: []) for name in ["DailyMarketReportFut", "DailyMarketReportOpt", "FinalSettlementPrice", "OpenInterestOfLargeTradersFutures", "OpenInterestOfLargeTradersOptions", "PutCallRatio", "BlockTrade"]}
    res=execute_taifex_openapi_refresh(
        operator_confirmed=a.confirm,
        requested_contexts=_csv(a.contexts),
        requested_products=_csv(a.products),
        requested_contracts=contracts,
        requested_sessions=a.sessions,
        requested_trade_dates=a.trade_date,
        put_call_ratio_latest_n=a.pcr_latest_n,
        max_put_call_ratio_rows=a.max_pcr_rows,
        requested_delivery_months=a.delivery_month,
        final_settlement_latest_n_per_product=a.final_settlement_latest_n,
        max_final_settlement_rows=a.max_final_settlement_rows,
        max_block_trade_rows=a.max_block_trade_rows,
        max_large_trader_oi_rows=a.max_large_trader_oi_rows,
        fetchers=fixture_fetchers,
    )
    head=subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True).stdout.strip()
    summary={"evaluation_timestamp":res.get('started_at_utc'),"head":head,"requested_contexts":res.get('requested_contexts'),"requested_products":res.get('requested_products'),"overall_status":res.get('overall_status'),"raw_payload_retained":False,"endpoints":{}}
    for k,v in res.get('endpoint_results',{}).items():
        obs=v.get('observations',[])
        summary['endpoints'][k]={"endpoint_fetch_status":v.get('batch_status'),"endpoint_row_count":v.get('row_count_received'),"matching_row_count":v.get('matching_scope_rows'),"retained_row_count":v.get('row_count_retained'),"retention":v.get('retention'),"reported_trade_dates":v.get('reported_trade_dates'),"retained_trade_dates":v.get('retained_trade_dates'),"currentness_statuses":sorted({(o.get('currentness') or {}).get('status') for o in obs}),"session_labels_observed":sorted({o.get('source_session_label') for o in obs if o.get('source_session_label')}),"quotation_unit_caveats":sorted({c for o in obs for c in o.get('caveats',[]) if 'quotation' in c}),"sample_retained_observation":obs[0] if obs else None}
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
