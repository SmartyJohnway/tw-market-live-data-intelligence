from __future__ import annotations
import argparse, hashlib, json, os, re, shutil, subprocess, tempfile, time
from pathlib import Path
try:
    from scripts.json_schema_validation import check_schema, validate_json_schema
except ModuleNotFoundError:
    from json_schema_validation import check_schema, validate_json_schema
try:
    from scripts.m5d_publication_common import ROOT, CAND, DEST, validate_candidate, frontend_inventory, M5C_MANIFEST_SHA, M5C_FRONTEND_PACKAGE_SHA, M5C_AUDIT_SHA, M5C_CORRECTION_SHA
except ModuleNotFoundError:
    from m5d_publication_common import ROOT, CAND, DEST, validate_candidate, frontend_inventory, M5C_MANIFEST_SHA, M5C_FRONTEND_PACKAGE_SHA, M5C_AUDIT_SHA, M5C_CORRECTION_SHA

ACTION = "publish_frontend_market_context"
SAFE_ID = re.compile(r"^[A-Za-z0-9_.:-]+$")
FALSE_FLAGS = {"production_ready", "generated_write", "network_market_data_call", "trading_output", "recommendation_output", "realtime_claim", "publication_performed"}
SCHEMAS = {
    "decision": ROOT / "docs/authorization/m5e_publication_authorization_decision_schema.json",
    "token": ROOT / "docs/authorization/m5e_single_use_token_schema.json",
    "journal": ROOT / "docs/authorization/m5e_transaction_journal_schema.json",
    "publication_receipt": ROOT / "docs/authorization/m5e_publication_receipt_schema.json",
    "rollback_receipt": ROOT / "docs/authorization/m5e_rollback_receipt_schema.json",
    "recovery_state": ROOT / "docs/authorization/m5e_crash_recovery_state_schema.json",
}
LINEAGE = {
    "m5c_manifest_sha256": M5C_MANIFEST_SHA,
    "m5c_frontend_readonly_context_package_sha256": M5C_FRONTEND_PACKAGE_SHA,
    "m5c_supplemental_audit_sha256": M5C_AUDIT_SHA,
    "m5c_run_summary_destination_correction_sha256": M5C_CORRECTION_SHA,
}

def load(p: Path | str):
    return json.loads(Path(p).read_text())

def fsha(p: Path | str) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def canonical_hash(obj: dict, *, omit: set[str] | None = None) -> str:
    payload = {k: v for k, v in obj.items() if k not in (omit or set())}
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()

def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("short_write")
        view = view[written:]

def manifest_sha(cdir: Path = CAND) -> str:
    return fsha(ROOT / cdir / "sha256_manifest.json")

def candidate_market_context_sha(cdir: Path = CAND) -> str:
    return load(ROOT / cdir / "sha256_manifest.json")["files"]["market-context.json"]

def _fsync_dir(path: Path) -> None:
    if os.name == "nt":
        return
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

def durable_json_replace(path: Path, obj: dict) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(obj, indent=2, sort_keys=True).encode() + b"\n"
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        _write_all(fd, data); os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    _fsync_dir(path.parent)
    return hashlib.sha256(data).hexdigest()

def durable_copy(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = src.read_bytes()
    tmp = dest.with_name(f".{dest.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        _write_all(fd, data); os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, dest)
    _fsync_dir(dest.parent)

def _schema_errors(label: str, obj: dict) -> list[str]:
    return [f"{label}_schema:{e['code']}:{e['path']}" for e in validate_json_schema(obj, load(SCHEMAS[label]))]

def _assert_schema(label: str, obj: dict) -> None:
    errs = _schema_errors(label, obj)
    if errs:
        raise ValueError("schema validation failed: " + ",".join(errs))

def validate_auth(decision, token, *, now=None):
    now = now or int(time.time()); errs = []
    try: d = load(decision); t = load(token)
    except Exception as e: return [f"malformed_json:{e}"]
    errs += _schema_errors("decision", d) + _schema_errors("token", t)
    if errs: return errs
    computed_token_sha = canonical_hash(t, omit={"token_sha256"})
    if t.get("token_sha256") != computed_token_sha: errs.append("token_sha256_mismatch")
    if d.get("token_sha256") != computed_token_sha: errs.append("decision_token_sha256_binding_mismatch")
    if d.get("authorization_id") != t.get("authorization_id"): errs.append("authorization_token_binding_mismatch")
    if d.get("allowed_action") != ACTION or t.get("allowed_action") != ACTION: errs.append("wrong_action")
    if d.get("acknowledgement_required") is not True or d.get("operator_acknowledged") is not True: errs.append("acknowledgement_missing")
    if t.get("single_use") is not True or not t.get("single_use_id"): errs.append("single_use_token_required")
    if d.get("single_use_id") != t.get("single_use_id"): errs.append("single_use_id_mismatch")
    if int(d.get("expires_at_epoch", 0)) <= now or int(t.get("expires_at_epoch", 0)) <= now: errs.append("expired_token")
    if d.get("candidate_dir") != str(CAND): errs.append("candidate_dir_mismatch")
    if d.get("candidate_manifest_sha256") != manifest_sha(): errs.append("wrong_candidate_hash")
    for k in ["candidate_dir", "candidate_manifest_sha256", "destination", "frontend_baseline_sha256"]:
        if t.get(k) != d.get(k): errs.append("token_decision_binding_mismatch:" + k)
    if d.get("destination") != str(DEST): errs.append("wrong_destination")
    if d.get("frontend_baseline_sha256") != fsha(ROOT / CAND / "frontend_public_baseline.json"): errs.append("frontend_baseline_drift")
    for k, v in LINEAGE.items():
        if d.get("m5c_lineage_hashes", {}).get(k) != v: errs.append("m5c_lineage_drift:" + k)
        if t.get("m5c_lineage_hashes", {}).get(k) != v or t.get("m5c_lineage_hashes", {}).get(k) != d.get("m5c_lineage_hashes", {}).get(k):
            errs.append("token_m5c_lineage_binding_mismatch:" + k)
    def scan(o, p="$"):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in FALSE_FLAGS and v is not False: errs.append("forbidden_flag:" + p + "/" + k)
                scan(v, p + "/" + k)
        elif isinstance(o, list):
            for i, v in enumerate(o): scan(v, p + "/" + str(i))
    scan(d); scan(t)
    return errs

def _has_symlink_component(path: Path) -> bool:
    probe = Path(path.anchor) if path.is_absolute() else Path()
    for part in path.parts[1:] if path.is_absolute() else path.parts:
        probe = probe / part
        if probe.exists() and probe.is_symlink():
            return True
    return False

def safe_dest(dest):
    raw = ROOT / dest
    if raw.exists() and raw.is_symlink(): raise ValueError("symlink_target_forbidden")
    resolved = raw.resolve(); base = (ROOT / "frontend/public").resolve()
    if not str(resolved).startswith(str(base) + os.sep): raise ValueError("path_traversal_or_wrong_root")
    return resolved

def claim_once(claim_dir, auth_id):
    if not SAFE_ID.match(auth_id or ""): raise ValueError("unsafe_authorization_id")
    claim_dir = Path(claim_dir); claim_dir.mkdir(parents=True, exist_ok=True)
    path = claim_dir / (auth_id + ".used")
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        _write_all(fd, b"claimed\n"); os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_dir(claim_dir)
    return path

def _journal_state(auth_id, dest, candidate_manifest_sha256, new_sha256, *, simulation_mode, state="started"):
    return {"schema_version":"m5e_transaction_journal.v1","state":state,"auth_id":auth_id,"destination":str(dest),"candidate_sha256":candidate_manifest_sha256,"new_sha256":new_sha256,"publication_performed":False,"simulation_mode":simulation_mode,"destination_write_simulated":False}

def publish_transaction(src, dest, journal_dir, *, auth_id, claim_dir=None, expected_src_sha256=None, candidate_manifest_sha256=None, crash_at=None, simulation_mode=False):
    if claim_dir is None: raise ValueError("claim_dir_required")
    if not SAFE_ID.match(auth_id or ""): raise ValueError("unsafe_authorization_id")
    if not simulation_mode and (expected_src_sha256 is not None or candidate_manifest_sha256 is not None):
        raise ValueError("candidate_lineage_override_forbidden")
    src = Path(src); dest = Path(dest); journal_dir = Path(journal_dir); journal_dir.mkdir(parents=True, exist_ok=True)
    if simulation_mode:
        simulation_root = Path(journal_dir).resolve().parent
        resolved_dest = dest.resolve()
        repo_root = ROOT.resolve()
        if str(resolved_dest).startswith(str(repo_root) + os.sep):
            raise ValueError("simulation_destination_in_repo_forbidden")
        if not str(resolved_dest).startswith(str(simulation_root) + os.sep):
            raise ValueError("simulation_destination_outside_temporary_root")
    else:
        lexical_dest = dest if dest.is_absolute() else ROOT / dest
        expected_lexical = ROOT / DEST
        if lexical_dest.absolute() != expected_lexical.absolute():
            raise ValueError("production_destination_mismatch")
        if _has_symlink_component(lexical_dest):
            raise ValueError("symlink_target_forbidden")
        safe_dest(DEST)
    expected_src_sha256 = expected_src_sha256 if simulation_mode and expected_src_sha256 else candidate_market_context_sha()
    candidate_manifest_sha256 = candidate_manifest_sha256 if simulation_mode and candidate_manifest_sha256 else manifest_sha()
    data = src.read_bytes(); new_hash = hashlib.sha256(data).hexdigest()
    if new_hash != expected_src_sha256: raise ValueError("source_hash_mismatch")
    state = _journal_state(auth_id, dest, candidate_manifest_sha256, new_hash, simulation_mode=simulation_mode)
    claim_path = claim_once(claim_dir, auth_id)
    state.update(state="claimed", single_use_claim=str(claim_path))
    _assert_schema("journal", state); durable_json_replace(journal_dir / "journal.json", state)
    if crash_at == "before_temp_write": raise RuntimeError("crash:before_temp_write")
    tmp = dest.with_name("." + dest.name + ".tmp")
    fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
    try:
        _write_all(fd, data); os.fsync(fd)
    finally:
        os.close(fd)
    _fsync_dir(tmp.parent)
    state.update(state="after_temp_write", temp=str(tmp)); _assert_schema("journal", state); durable_json_replace(journal_dir / "journal.json", state)
    if crash_at == "after_temp_write": raise RuntimeError("crash:after_temp_write")
    if dest.exists():
        backup = journal_dir / "previous.bin"; durable_copy(dest, backup)
        state.update(state="after_backup", backup=str(backup), previous_sha256=fsha(backup)); _assert_schema("journal", state); durable_json_replace(journal_dir / "journal.json", state)
    if crash_at == "after_backup": raise RuntimeError("crash:after_backup")
    os.replace(tmp, dest); _fsync_dir(dest.parent)
    state.update(state="after_replace", publication_performed=False if simulation_mode else True, destination_write_simulated=True if simulation_mode else False); _assert_schema("journal", state); durable_json_replace(journal_dir / "journal.json", state)
    if crash_at in {"after_replace", "before_receipt"}: raise RuntimeError("crash:" + crash_at)
    out = {"schema_version":"m5e_publication_receipt.v1","status":"simulated" if simulation_mode else "published","authorization_id":auth_id,"destination":str(dest),"sha256":fsha(dest),"candidate_manifest_sha256":candidate_manifest_sha256,"publication_performed":False if simulation_mode else True,"single_use_claim":state.get("single_use_claim")}
    if simulation_mode: out["simulation_mode"] = True
    if state.get("previous_sha256"): out["previous_sha256"] = state["previous_sha256"]
    _assert_schema("publication_receipt", out); durable_json_replace(journal_dir / "publication_receipt.json", out)
    state.update(state="after_receipt", receipt=str(journal_dir / "publication_receipt.json")); _assert_schema("journal", state); durable_json_replace(journal_dir / "journal.json", state)
    if crash_at == "after_receipt": raise RuntimeError("crash:after_receipt")
    return out

def rollback(dest, journal_dir):
    dest = Path(dest); st = load(Path(journal_dir) / "journal.json")
    if st.get("backup") and Path(st["backup"]).exists():
        if not dest.exists() or fsha(dest) != st.get("new_sha256"):
            out = {"schema_version":"m5e_rollback_receipt.v1","status":"manual_recovery_required","destination":str(dest),"rollback_performed":False,"state":st}
        else:
            durable_copy(Path(st["backup"]), dest)
            out = {"schema_version":"m5e_rollback_receipt.v1","status":"rolled_back_replacement","destination":str(dest),"rollback_performed":True,"sha256":fsha(dest)}
    elif (st.get("publication_performed") or st.get("destination_write_simulated")) and dest.exists() and fsha(dest) == st.get("new_sha256"):
        dest.unlink(); _fsync_dir(dest.parent)
        out = {"schema_version":"m5e_rollback_receipt.v1","status":"rolled_back_new_target","destination":str(dest),"rollback_performed":True}
    else:
        out = {"schema_version":"m5e_rollback_receipt.v1","status":"manual_recovery_required","destination":str(dest),"rollback_performed":False,"state":st}
    _assert_schema("rollback_receipt", out)
    durable_json_replace(Path(journal_dir) / "rollback_receipt.json", out)
    return out

def recover(dest, journal_dir):
    st = load(Path(journal_dir) / "journal.json")
    if st.get("state") in {"started", "claimed", "after_temp_write"}:
        out = {"schema_version":"m5e_crash_recovery_state.v1","status":"safe_no_publication_or_temp_only","state":st}
    elif st.get("state") == "after_backup" and st.get("previous_sha256") and Path(dest).exists() and fsha(dest) == st.get("previous_sha256"):
        out = {"schema_version":"m5e_crash_recovery_state.v1","status":"safe_no_publication_or_temp_only","state":st}
    elif st.get("state") == "after_backup":
        rb = rollback(dest, journal_dir); out = {"schema_version":"m5e_crash_recovery_state.v1","status":rb["status"],"state":st}
    elif st.get("state") == "after_receipt":
        receipt_path = Path(st.get("receipt", ""))
        if receipt_path.exists():
            receipt = load(receipt_path)
            receipt_ok = not _schema_errors("publication_receipt", receipt)
            dest_ok = Path(dest).exists() and fsha(dest) == st.get("new_sha256") == receipt.get("sha256")
            binding_ok = (receipt.get("candidate_manifest_sha256") == st.get("candidate_sha256") and receipt.get("authorization_id") == st.get("auth_id") and receipt.get("destination") == st.get("destination") == str(dest) and receipt.get("single_use_claim") == st.get("single_use_claim"))
            completed = "simulation_completed" if receipt.get("simulation_mode") is True else "publication_completed"
            out = {"schema_version":"m5e_crash_recovery_state.v1","status":completed if (receipt_ok and dest_ok and binding_ok) else "manual_recovery_required","state":st}
        else:
            out = {"schema_version":"m5e_crash_recovery_state.v1","status":"manual_recovery_required","state":st}
    else:
        out = {"schema_version":"m5e_crash_recovery_state.v1","status":"manual_recovery_required","state":st}
    _assert_schema("recovery_state", out)
    durable_json_replace(Path(journal_dir) / "recovery_state.json", out)
    return out

def changed_paths_against_base():
    candidates = []
    base_ref = os.environ.get("GITHUB_BASE_REF")
    if base_ref: candidates.append(f"origin/{base_ref}...HEAD")
    candidates += ["origin/main...HEAD", "HEAD~1..HEAD"]
    for spec in candidates:
        r = subprocess.run(["git", "diff", "--name-only", spec], cwd=ROOT, text=True, capture_output=True)
        if r.returncode == 0: return [p for p in r.stdout.splitlines() if p]
    return subprocess.check_output(["git", "diff", "--name-only", "HEAD"], cwd=ROOT, text=True).splitlines()

def validate_schemas_and_outputs() -> bool:
    if any(check_schema(load(p)) for p in SCHEMAS.values()): return False
    with tempfile.TemporaryDirectory() as td:
        t = Path(td); src = ROOT / CAND / "market-context.json"; dest = t / "dest.json"; j = t / "journal"; claims = t / "claims"
        receipt = publish_transaction(src, dest, j, auth_id="schema-gate", claim_dir=claims, simulation_mode=True, expected_src_sha256=candidate_market_context_sha(), candidate_manifest_sha256=manifest_sha())
        if _schema_errors("publication_receipt", receipt): return False
        rb = rollback(dest, j)
        if _schema_errors("rollback_receipt", rb): return False
        dest.write_text("old"); j2 = t / "journal2"
        try: publish_transaction(src, dest, j2, auth_id="schema-gate2", claim_dir=claims, crash_at="after_backup", simulation_mode=True, expected_src_sha256=candidate_market_context_sha(), candidate_manifest_sha256=manifest_sha())
        except RuntimeError: pass
        rec = recover(dest, j2)
        if _schema_errors("recovery_state", rec): return False
    return True

def check_only():
    checks = {}
    checks["m5d_candidate_validation"] = not validate_candidate(CAND)
    report = load(ROOT / "docs/release/M5E_RUNTIME_CONSUMER_COMPATIBILITY_REPORT.json")
    checks["runtime_consumer_compatibility"] = report.get("market_context_json_loaded_by_current_public_ui") is False and "m5e-market-context-adapter.js" in report.get("rendering_path", "")
    checks["schema_validation"] = validate_schemas_and_outputs()
    checks["authorization_absence"] = not (ROOT / "docs/authorization/decisions/M5E_FRONTEND_PUBLICATION_AUTHORIZATION.json").exists() and not (ROOT / "docs/authorization/tokens").exists()
    with tempfile.TemporaryDirectory() as td:
        t = Path(td); src = ROOT / CAND / "market-context.json"; dest = t / "dest"; dest.write_text("old"); j = t / "j"; claims = t / "claims"
        publish_transaction(src, dest, j, auth_id="gate", claim_dir=claims, simulation_mode=True, expected_src_sha256=candidate_market_context_sha(), candidate_manifest_sha256=manifest_sha()); checks["transaction_simulation"] = fsha(dest) == candidate_market_context_sha()
        checks["rollback_simulation"] = rollback(dest, j).get("status") == "rolled_back_replacement" and dest.read_text() == "old"
        dest.write_text("old2"); j2 = t / "j2"
        try: publish_transaction(src, dest, j2, auth_id="gate2", claim_dir=claims, crash_at="after_backup", simulation_mode=True, expected_src_sha256=candidate_market_context_sha(), candidate_manifest_sha256=manifest_sha())
        except RuntimeError: pass
        checks["crash_recovery_simulation"] = recover(dest, j2).get("status") == "safe_no_publication_or_temp_only"
    forbidden_prefixes = ("frontend/public", "research/generated", "research/live_probe_runs/m5b", "research/staging/m5c", "production", "prod", "broker", "credentials", "tokens", ".env")
    checks["forbidden_path_scan"] = not any(p.startswith(forbidden_prefixes) for p in changed_paths_against_base())
    ready = False
    return {"checks":checks,"status":"superseded_by_m5f","superseded_by_m5f":True,"ready_for_explicit_user_authorization_review":ready,"frontend_publication_authorized":False,"publication_performed":False,"execute_mode_available":False,"production_ready":False,"candidate_manifest_sha256":manifest_sha(),"runtime_consumer_compatible":checks["runtime_consumer_compatibility"],"authorization_absent":checks["authorization_absence"],"statement":"M5D frontend publication gate is superseded by M5F canonical package and cannot be authorized."}

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--check-only", action="store_true"); ap.add_argument("--execute-publication", action="store_true"); ap.add_argument("--authorization-decision"); ap.add_argument("--token"); ns = ap.parse_args(argv)
    if not ns.execute_publication:
        out = check_only(); print(json.dumps(out, indent=2, sort_keys=True)); return 0
    if not (ns.authorization_decision and ns.token): print(json.dumps({"status":"blocked","errors":["authorization_decision_and_token_required"],"publication_performed":False})); return 2
    errs = validate_candidate(CAND) + validate_auth(ns.authorization_decision, ns.token)
    try: safe_dest(DEST)
    except Exception as e: errs.append(str(e))
    if errs: print(json.dumps({"status":"blocked","errors":errs,"publication_performed":False}, indent=2)); return 2
    print(json.dumps({"status":"blocked","errors":["repository_level_execution_disabled_without_real_authorization_ceremony"],"publication_performed":False}, indent=2)); return 2
if __name__ == "__main__": raise SystemExit(main())
