import json
from scripts.validate_m5c_run_summary_destination_correction import CORRECTION, validate

def test_run_summary_destination_correction_validates():
    assert validate()==[]

def test_run_summary_destination_correction_blocks_tamper(tmp_path):
    data=json.loads(CORRECTION.read_text())
    data['recorded_value']='research/staging/m5c/m5c_twse_openapi_20260627_authorized_01'
    p=tmp_path/'correction.json'; p.write_text(json.dumps(data))
    assert validate(p)
