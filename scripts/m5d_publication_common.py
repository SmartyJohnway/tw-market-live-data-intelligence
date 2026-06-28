from __future__ import annotations
import hashlib, json, os, shutil, subprocess, tempfile
from pathlib import Path

try:
    from validate_m5c_promoted_staging_package import validate as validate_m5c_package
except ModuleNotFoundError:
    from scripts.validate_m5c_promoted_staging_package import validate as validate_m5c_package

ROOT = Path(__file__).resolve().parents[1]
M5C = Path('research/staging/m5c/m5c_twse_openapi_20260627_authorized_01')
CAND = Path('research/staging/m5d/m5d_frontend_publication_candidate_01')
DEST = Path('frontend/public/market-context.json')
REQ = Path('docs/authorization/requests/M5D_FRONTEND_PUBLICATION_REQUEST.json')
AUDIT = Path('research/staging/m5c/supplemental_audit/M5C_TWSE_OPENAPI_STAGING_PROMOTION_AUTHORIZED_01_AUDIT.json')
CORR = Path('research/staging/m5c/corrections/M5C_RUN_SUMMARY_DESTINATION_CORRECTION_20260627_01.json')
PR57_MERGE_SHA = '3931f19564698926a96a3022c5c3b40b07de6081'
TARGETS = ['2330', '0050', '00929']
M5C_MANIFEST_SHA = '9956b27850f2561f3738ebacda350b1685d54e1947910191605be637ad7dd203'
M5C_FRONTEND_PACKAGE_SHA = 'a21c0436c11481cd452fbe42e71ae944d4d76ec422e45924fab6428fab030048'
M5C_AUDIT_SHA = '447e5b2435c885c1fae8744224551ab1efa675cbebee5ea15e41d95b855dea0a'
M5C_CORRECTION_SHA = 'c8cbfebacbeabf530f50a7abaed3fe51ec597e329f7eb64b94bdcbab1aa6f306'
REQUIRED_ARTIFACTS = {
    'candidate_summary.json', 'frontend_public_baseline.json', 'market-context.json',
    'publication_plan.json', 'rollback_plan.json', 'source_binding.json',
    'validation_report.json', 'sha256_manifest.json'
}
FORBIDDEN_FALSE_FLAGS = [
    'realtime_guaranteed', 'trading_signal', 'production_ready', 'publication_performed',
    'frontend_public_write', 'actual_frontend_publication_authorized'
]

def sha(p: Path) -> str:
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()

def load(p: Path):
    return json.loads((ROOT / p).read_text())

def dump(p: Path, d):
    path = ROOT / p
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n")

def _git_is_ancestor(commit: str) -> bool:
    return subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'HEAD'], cwd=ROOT).returncode == 0

def frontend_inventory():
    base = ROOT / 'frontend/public'
    rows = []
    if base.exists():
        for p in sorted(x for x in base.rglob('*') if x.is_file()):
            rel = p.relative_to(base).as_posix()
            is_target = rel == 'market-context.json'
            rows.append({
                'relative_path': rel,
                'sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
                'size_bytes': p.stat().st_size,
                'target_path_exists': is_target,
                'overwrite_required': is_target,
                'rollback_required': is_target,
            })
    target_exists = (ROOT / DEST).exists()
    return {
        'schema_version': 'm5d_frontend_public_baseline.v1',
        'baseline_root': 'frontend/public',
        'hash_only': True,
        'files': rows,
        'target_path': 'frontend/public/market-context.json',
        'target_path_exists': target_exists,
        'overwrite_required': target_exists,
        'rollback_required': target_exists,
    }

def _current_artifact_hashes(c: Path) -> dict[str, str]:
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / c).glob('*.json')) if p.name != 'sha256_manifest.json'}

def verify_upstream():
    errs = []
    if not _git_is_ancestor(PR57_MERGE_SHA):
        errs.append('pr57_merge_sha_not_head_ancestor')
    if sha(M5C / 'sha256_manifest.json') != M5C_MANIFEST_SHA:
        errs.append('m5c_manifest_sha_mismatch')
    if sha(M5C / 'frontend_readonly_context_package.json') != M5C_FRONTEND_PACKAGE_SHA:
        errs.append('m5c_frontend_package_sha_mismatch')
    if sha(AUDIT) != M5C_AUDIT_SHA:
        errs.append('m5c_supplemental_audit_sha_mismatch')
    if sha(CORR) != M5C_CORRECTION_SHA:
        errs.append('m5c_run_summary_destination_correction_sha_mismatch')
    man = load(M5C / 'sha256_manifest.json')
    if man.get('targets') != TARGETS:
        errs.append('targets_mismatch')
    src = load(M5C / 'frontend_readonly_context_package.json')
    if {s.get('source_id') for s in src.get('sources', [])} != {'TWSE_OpenAPI'}:
        errs.append('source_mismatch')
    errs.extend(validate_m5c_package(M5C))
    return errs

def build():
    errs = verify_upstream()
    if errs:
        raise SystemExit('upstream integrity failed: ' + ','.join(map(str, errs)))
    src = load(M5C / 'frontend_readonly_context_package.json')
    bindings = {
        'm5c_package_dir': str(M5C),
        'm5c_manifest_sha256': M5C_MANIFEST_SHA,
        'm5c_frontend_readonly_context_package_sha256': M5C_FRONTEND_PACKAGE_SHA,
        'm5c_supplemental_audit_sha256': M5C_AUDIT_SHA,
        'm5c_run_summary_destination_correction_sha256': M5C_CORRECTION_SHA,
        'pr57_merge_sha': PR57_MERGE_SHA,
        'source': 'TWSE_OpenAPI',
        'targets': TARGETS,
    }
    common = {
        'schema_version': 'm5d_frontend_publication_candidate.v1',
        'candidate_dir': str(CAND),
        'proposed_destination': str(DEST),
        'publication_performed': False,
        'frontend_public_write': False,
        'actual_frontend_publication_authorized': False,
        'production_ready': False,
        'realtime_guaranteed': False,
        'trading_signal': False,
        'readonly_only': True,
        'historical_evidence_snapshot': True,
        'stale_status': 'stale',
        'badge': 'historical/stale',
        'no_temporary_paths': True,
    }
    dump(CAND / 'market-context.json', {**src, **common, 'schema_version': 'm5d_market_context.v1', 'derived_from': 'reviewed_m5c_frontend_readonly_context_package', 'bindings': bindings})
    dump(CAND / 'source_binding.json', {**common, **bindings})
    dump(CAND / 'frontend_public_baseline.json', frontend_inventory())
    dump(CAND / 'candidate_summary.json', {**common, 'ready_for_user_authorization_review': True, 'frontend_publication_authorized': False, 'symbols': TARGETS, 'authority': 'TWSE_OpenAPI', 'caveats': src.get('global_caveats', [])})
    dump(CAND / 'validation_report.json', {**common, 'status': 'pass', 'checks': ['upstream_integrity', 'baseline_hash_only', 'readonly_stale_caveats', 'no_temp_paths', 'forbidden_flags', 'frontend_public_baseline_drift']})
    dump(CAND / 'rollback_plan.json', {**common, 'simulation_only': True, 'rollback_required': (ROOT / DEST).exists(), 'steps': ['restore previous destination hash from baseline if overwritten in future authorized execution', 'remove newly created destination if no baseline existed']})
    dump(CAND / 'publication_plan.json', {**common, 'request_only': True, 'next_required_action': 'user_authorization', 'execution_available': False, 'fail_closed_reason': 'no authorization decision or token exists'})
    manifest = {'schema_version': 'm5d_sha256_manifest.v1', 'candidate_dir': str(CAND), 'manifest_final': True, 'files': _current_artifact_hashes(CAND), **common, **bindings}
    dump(CAND / 'sha256_manifest.json', manifest)
    req = {'schema_version': 'm5d_frontend_publication_request.v2', 'request_id': 'M5D_FRONTEND_PUBLICATION_REQUEST', 'candidate_dir': str(CAND), 'candidate_manifest_sha256': sha(CAND / 'sha256_manifest.json'), 'proposed_destination': str(DEST), 'm5c_staging_package_dir': str(M5C), 'm5c_staging_manifest_sha256': M5C_MANIFEST_SHA, 'single_use': True, 'request_only': True, 'authorization_token_issued': False, 'actual_frontend_publication_authorized': False, 'publication_performed': False, 'next_required_action': 'user_authorization'}
    dump(REQ, req)
    return manifest

def _scan_forbidden_flags(obj, path='$'):
    errs = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in FORBIDDEN_FALSE_FLAGS and v is not False:
                errs.append(f'forbidden_flag:{path}/{k}')
            errs.extend(_scan_forbidden_flags(v, f'{path}/{k}'))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            errs.extend(_scan_forbidden_flags(v, f'{path}/{i}'))
    return errs

def validate_candidate(cdir=CAND):
    errs = []
    c = Path(cdir)
    c_abs = ROOT / c
    if not c_abs.exists():
        return ['candidate_dir_missing']
    artifact_names = {p.name for p in c_abs.glob('*.json')}
    if artifact_names != REQUIRED_ARTIFACTS:
        errs.append('artifact_set_mismatch')
    man = load(c / 'sha256_manifest.json')
    if man.get('manifest_final') is not True:
        errs.append('manifest_final_not_true')
    if man.get('candidate_dir') != str(CAND):
        errs.append('candidate_dir_mismatch')
    if man.get('proposed_destination') != str(DEST):
        errs.append('proposed_destination_mismatch')
    if man.get('pr57_merge_sha') != PR57_MERGE_SHA:
        errs.append('pr57_merge_sha_mismatch')
    expected_bindings = {
        'm5c_manifest_sha256': M5C_MANIFEST_SHA,
        'm5c_frontend_readonly_context_package_sha256': M5C_FRONTEND_PACKAGE_SHA,
        'm5c_supplemental_audit_sha256': M5C_AUDIT_SHA,
        'm5c_run_summary_destination_correction_sha256': M5C_CORRECTION_SHA,
        'source': 'TWSE_OpenAPI',
        'targets': TARGETS,
        'm5c_package_dir': str(M5C),
    }
    for k, v in expected_bindings.items():
        if man.get(k) != v:
            errs.append(f'binding_mismatch:{k}')
    current_hashes = _current_artifact_hashes(c)
    if set(man.get('files', {})) != (REQUIRED_ARTIFACTS - {'sha256_manifest.json'}):
        errs.append('manifest_file_set_mismatch')
    for name, h in man.get('files', {}).items():
        if current_hashes.get(name) != h:
            errs.append('candidate_payload_tampering:' + name)
    mc = load(c / 'market-context.json')
    for k, v in expected_bindings.items():
        if mc.get('bindings', {}).get(k) != v:
            errs.append(f'market_context_binding_mismatch:{k}')
    for caveat in ['not_realtime_guaranteed', 'not_trading_signal', 'not_production_current_state', 'freshness_must_be_displayed']:
        if caveat not in mc.get('global_caveats', []):
            errs.append('missing_caveat:' + caveat)
    text = '\n'.join((ROOT / p).read_text() for p in c.glob('*.json'))
    if '/tmp/' in text or '.m5c_tmp_' in text:
        errs.append('temporary_path_leakage')
    for artifact in sorted(artifact_names):
        errs.extend(_scan_forbidden_flags(load(c / artifact), '$/' + artifact))
    if sha(M5C / 'frontend_readonly_context_package.json') != man.get('m5c_frontend_readonly_context_package_sha256'):
        errs.append('source_package_changed_after_candidate_build')
    if frontend_inventory() != load(c / 'frontend_public_baseline.json'):
        errs.append('frontend_public_baseline_drift')
    errs.extend(verify_upstream())
    return errs
