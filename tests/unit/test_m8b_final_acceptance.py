from pathlib import Path
import json
def test_m8b_final_acceptance_and_registry():
 doc=Path('docs/protocol/M8B_01_TAIFEX_OPENAPI_OFFICIAL_DERIVATIVES_EOD_FINAL_ACCEPTANCE.md').read_text()
 assert 'm8b_01_taifex_openapi_official_derivatives_eod_context_pass_with_caveats' in doc
 reg=json.load(open('docs/data_capabilities/m8_source_capability_registry.json'))
 s=next(x for x in reg['sources'] if x['source_id']=='TAIFEX_OPENAPI')
 assert s['runtime_available'] and s['runtime_executable'] and s['adapter_implemented'] and s['bounded_retained_scope']
