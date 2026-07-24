import json
from pathlib import Path
def test_schema_json(): assert json.loads(Path('schemas/unified_market_evidence_execution_authorization.v1.schema.json').read_text())['title']
