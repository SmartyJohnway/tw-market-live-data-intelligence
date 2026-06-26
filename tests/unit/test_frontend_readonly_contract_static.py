import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))

def test_adapter_preserves_schema_words():
    text=(ROOT/'frontend/readonly-preview/readonlyContextAdapter.js').read_text()
    for word in ['source_id','source_authority','freshness_status','delay_status','staleness_seconds','retrieved_at','source_timestamp','data_quality_flags','source_risk_flags','display_caveats']:
        assert word in text
    assert 'not realtime guaranteed' in text and 'not a trading signal' in text and 'not production current state' in text
