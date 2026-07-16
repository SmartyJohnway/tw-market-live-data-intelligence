#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.m8r_03e_watchlist_ai_context_builder import build_watchlist_ai_context_package, build_context_manifest, render_watchlist_ai_context_preview
from scripts.m8r_03e_conversation_handoff_builder import build_watchlist_conversation_handoff
from scripts.m8r_03e_context_validator import validate_watchlist_ai_context_package, validate_watchlist_conversation_handoff, validate_watchlist_ai_context_manifest, validate_m8r_03e_upstream_artifacts
from scripts.m8r_filesystem_safety import FilesystemSafetyError, atomic_write_text, safe_destination, validate_authorized_root

def _reject_url(p):
    if '://' in str(p): raise ValueError('url_input_rejected')
    return Path(p)
def load(p): return json.loads(_reject_url(p).read_text(encoding='utf-8'))
def _safe_root(root):
    return validate_authorized_root(root)
def atomic_write(path:Path, text:str):
    root = getattr(atomic_write, '_authorized_root', path.parent)
    rel = path.relative_to(root)
    atomic_write_text(root, rel, text)
def dump(path,obj): atomic_write(path,json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2)+'\n')

def main(argv=None):
    ap=argparse.ArgumentParser(); ap.add_argument('--request',required=True); ap.add_argument('--execution-plan',required=True); ap.add_argument('--execution-result',required=True); ap.add_argument('--bundle',required=True); ap.add_argument('--output-root',required=True); ap.add_argument('--generated-at-utc',required=True); ap.add_argument('--context-policy'); ap.add_argument('--allow-overwrite',action='store_true')
    a=ap.parse_args(argv)
    try:
        req,plan,res,bundle=load(a.request),load(a.execution_plan),load(a.execution_result),load(a.bundle); policy=load(a.context_policy) if a.context_policy else None
        out=_safe_root(a.output_root); run_name='m8r03e-'+a.generated_at_utc.replace(':','').replace('-','')
        run_dest=safe_destination(out, run_name, create_parent=False)
        run=run_dest.path
        if run.exists() and not a.allow_overwrite: raise FileExistsError('output_run_directory_exists')
        run.mkdir(parents=True,exist_ok=a.allow_overwrite)
        atomic_write._authorized_root = out
        uv=validate_m8r_03e_upstream_artifacts(validated_request=req,execution_plan=plan,execution_result=res,watchlist_bundle=bundle)
        if not uv['valid']: raise ValueError('upstream_artifact_validation_failed')
        pkg=build_watchlist_ai_context_package(validated_request=req,execution_plan=plan,execution_result=res,watchlist_bundle=bundle,generated_at_utc=a.generated_at_utc,context_policy=policy)
        hand=build_watchlist_conversation_handoff(context_package=pkg,generated_at_utc=a.generated_at_utc)
        upstream={'validated_request':req,'execution_plan':plan,'execution_result':res,'watchlist_bundle':bundle}
        man=build_context_manifest(context_package=pkg,conversation_handoff=hand,upstream_artifacts=upstream,generated_at_utc=a.generated_at_utc)
        preview=render_watchlist_ai_context_preview(pkg)
        vp=validate_watchlist_ai_context_package(pkg,upstream_artifacts=upstream)
        vh=validate_watchlist_conversation_handoff(hand,context_package=pkg); vm=validate_watchlist_ai_context_manifest(man,context_package=pkg,handoff=hand,upstream_artifacts=upstream)
        if not (vp['valid'] and vh['valid'] and vm['valid']):
            man['validation_status']='failed'; man['validation_issues']=vp['issues']+vh['issues']+vm['issues']
        dump(run/'watchlist_ai_context.json',pkg); dump(run/'watchlist_conversation_handoff.json',hand); dump(run/'watchlist_ai_context_manifest.json',man); atomic_write(run/'watchlist_ai_context_preview.md',preview)
        # re-read and validate hashes
        pkg2=load(run/'watchlist_ai_context.json'); hand2=load(run/'watchlist_conversation_handoff.json'); man2=load(run/'watchlist_ai_context_manifest.json')
        ok=validate_watchlist_ai_context_package(pkg2,upstream_artifacts=upstream)['valid'] and validate_watchlist_conversation_handoff(hand2,context_package=pkg2)['valid'] and validate_watchlist_ai_context_manifest(man2,context_package=pkg2,handoff=hand2,upstream_artifacts=upstream)['valid']
        print(json.dumps({'status':'success' if ok and man2['validation_status']=='passed' else 'failed','output_dir':str(run),'coverage_status':pkg2['coverage_summary']['coverage_status'],'validation_status':man2['validation_status']},sort_keys=True))
        return 0 if ok and man2['validation_status']=='passed' else 2
    except Exception as e:
        code = e.code if isinstance(e, FilesystemSafetyError) else str(e).split(':')[0]
        print(json.dumps({'status':'artifact_write_failed' if isinstance(e,(OSError,FileExistsError,FilesystemSafetyError)) else 'failed','reason_code':code},sort_keys=True),file=sys.stderr); return 1
if __name__=='__main__': raise SystemExit(main())
