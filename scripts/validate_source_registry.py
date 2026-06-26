import argparse,json
from pathlib import Path
def validate_source_registry(reg,cat,schema,cov):
 e=[]; flags={x['risk_flag'] for x in cat.get('risk_flags',[])}; fields=set(schema.get('required_source_fields',[]))
 for s in reg.get('sources',[]):
  miss=fields-set(s);
  if miss:e.append({'code':'missing_source_fields','source_id':s.get('source_id'),'fields':sorted(miss)})
  for f in s.get('risk_flags',[]):
   if f not in flags:e.append({'code':'unknown_risk_flag','source_id':s.get('source_id'),'flag':f})
  if s.get('production_current_state_allowed') is not False:e.append({'code':'production_not_allowed','source_id':s.get('source_id')})
 return e
def main(argv=None):
 ap=argparse.ArgumentParser(); ap.add_argument('--registry',default='docs/source_registry/source_authority_registry.json'); ap.add_argument('--catalog',default='docs/source_registry/source_risk_flag_catalog.json'); ap.add_argument('--schema',default='docs/source_registry/source_contract_schema.json'); ap.add_argument('--coverage',default='docs/source_registry/source_family_coverage_matrix.json'); a=ap.parse_args(argv); errs=validate_source_registry(*(json.loads(Path(p).read_text()) for p in [a.registry,a.catalog,a.schema,a.coverage])); print(json.dumps({'ok':not errs,'errors':errs},indent=2)); return 0 if not errs else 1
if __name__=='__main__': raise SystemExit(main())
