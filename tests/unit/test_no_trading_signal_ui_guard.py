import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))

import re
ALLOWED=['not a trading signal','no trading signal','no trading interpretation','not realtime guaranteed','no realtime guarantee']
def cleaned(line):
    l=line.lower()
    for a in ALLOWED: l=l.replace(a,'')
    return l
def test_no_positive_trading_or_realtime_claims():
    forbidden=['buy','sell','hold','target price','recommendation','rank','score','trading signal','official realtime','realtime guaranteed']
    for p in (ROOT/'frontend/readonly-preview').glob('*'):
        for i,line in enumerate(p.read_text(encoding="utf-8").splitlines(),1):
            c=cleaned(line)
            assert not any(re.search(r'\b'+re.escape(term)+r'\b', c) for term in forbidden), f'{p}:{i}:{line}'
