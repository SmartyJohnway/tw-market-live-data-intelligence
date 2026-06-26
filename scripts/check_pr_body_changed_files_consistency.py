"""Check that PR body Actual changed files entries match the real git diff list."""
from __future__ import annotations
import argparse, json, re, sys
from dataclasses import dataclass
@dataclass
class ConsistencyResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    listed_files: list[str]
def _extract(pr_body:str)->list[str]|None:
    m=re.search(r"^#+\s*Actual changed files\s*$", pr_body, re.I|re.M)
    if not m: return None
    tail=pr_body[m.end():]
    next_h=re.search(r"^#+\s+", tail, re.M)
    block=tail[:next_h.start()] if next_h else tail
    files=[]
    for line in block.splitlines():
        s=line.strip().strip('`')
        if not s or s.startswith('```'): continue
        s=re.sub(r"^[-*]\s+",'',s).strip().strip('`')
        if s and not s.startswith('#'): files.append(s)
    return files
def check_pr_body_changed_files_consistency(pr_body:str, changed_files:list[str])->ConsistencyResult:
    listed=_extract(pr_body)
    if listed is None: return ConsistencyResult(False,["missing Actual changed files section"],[],[])
    changed=set(changed_files); errors=[]; warnings=[]
    seen=set(); dups=[]
    for f in listed:
        if f in seen: dups.append(f)
        seen.add(f)
        if f not in changed: errors.append(f"listed file not in changed files: {f}")
    if dups: warnings.append("duplicate file entries: "+", ".join(sorted(set(dups))))
    missing=sorted(changed-set(listed))
    if missing: warnings.append("changed files missing from PR body: "+", ".join(missing))
    return ConsistencyResult(not errors, errors, warnings, listed)
def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--pr-body',required=True); ap.add_argument('--changed-files',nargs='*',default=[]); ap.add_argument('--json',action='store_true')
    a=ap.parse_args(argv); r=check_pr_body_changed_files_consistency(open(a.pr_body,encoding='utf-8').read(),a.changed_files)
    print(json.dumps(r.__dict__,indent=2) if a.json else r); return 0 if r.ok else 1
if __name__=='__main__': raise SystemExit(main())
