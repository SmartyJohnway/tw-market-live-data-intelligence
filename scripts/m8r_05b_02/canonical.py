"""Deterministic canonical JSON identities for M8R-05B-02."""
import hashlib,json

def canonical_json(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha256_json(value): return hashlib.sha256(canonical_json(value).encode()).hexdigest()
def authorization_identity(scope):
 d=sha256_json(scope); return d,'umea-v1-'+d[:20]
