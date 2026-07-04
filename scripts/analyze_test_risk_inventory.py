#!/usr/bin/env python3
"""Static test-risk inventory and conservative duplicate-cluster analyzer.

This script does not execute tests or import application modules. It parses test
files with the Python AST and emits advisory inventory artifacts for human review.
"""
from __future__ import annotations

import argparse
import ast
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Iterable

INVENTORY_COLUMNS = [
    "test_file","test_function","line_number","decorators","pytest_markers","is_parametrized",
    "parametrize_case_count_estimate","imported_modules","called_functions","assert_count",
    "assertion_keyword_summary","string_constant_summary","risk_tags","risk_cluster_key",
    "likely_authoritative_owner","recommended_review_action","notes",
]
CLUSTER_COLUMNS = [
    "risk_cluster_key","risk_tags","cluster_size","candidate_owner","candidate_duplicates",
    "semantic_equivalence_guess","safe_to_auto_retire","reason",
]
OWNER_HINTS = {
    "m5f_canonical": "tests/unit/test_m5f_canonical_market_context_package.py",
    "observation_not_canonical": "tests/unit/test_m5k_workflow.py",
    "bounded_watchlist": "tests/unit/test_m5k_workflow.py",
    "no_full_market_scan": "tests/unit/test_m5b_execution_authorization.py",
    "no_trading_semantics": "scripts/forbidden_behavior_scanner.py",
    "raw_payload_leakage": "scripts/forbidden_behavior_scanner.py",
    "ssl_policy": "scripts/ssl_policy.py",
    "invalid_ssl_fail_closed": "tests/unit/test_m6d_operator_and_local_networking.py",
    "fastapi_execute_confirmation": "tests/unit/test_m6d_operator_and_local_networking.py",
    "mcp_fail_closed": "tests/unit/test_mcp_server.py",
    "source_health": "tests/test_m5q_source_health.py",
    "conversation_context": "tests/unit/test_m5n_watchlist_workflow.py",
    "m6e_acceptance": "tests/test_m6e_operator_acceptance.py",
    "m6g_browser_e2e": "tests/test_m6g_browser_operator_e2e.py",
    "governance_path": "scripts/governance_forbidden_path_guard.py",
    "forbidden_behavior": "scripts/forbidden_behavior_scanner.py",
}
SAFETY_CRITICAL = {"m5f_canonical","ssl_policy","invalid_ssl_fail_closed","m6e_acceptance","m6g_browser_e2e","raw_payload_leakage","no_trading_semantics","governance_path","forbidden_behavior","bounded_watchlist","mcp_fail_closed","fastapi_execute_confirmation"}

@dataclass
class TestRow:
    values: dict[str, str]
    assertion_fingerprint: str
    tautological: bool


def unparse(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return type(node).__name__


def csv_join(items: Iterable[str]) -> str:
    return ";".join(sorted({i for i in items if i}))


def decorator_name(dec: ast.AST) -> str:
    if isinstance(dec, ast.Call):
        return unparse(dec.func)
    return unparse(dec)


def call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return call_name(node.func)
    return None


def const_strings(node: ast.AST) -> list[str]:
    out = []
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            s = " ".join(n.value.split())
            if s:
                out.append(s[:80])
    return out


def imports(tree: ast.AST) -> list[str]:
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out.extend(alias.name for alias in n.names)
        elif isinstance(n, ast.ImportFrom) and n.module:
            out.append(n.module)
    return out


def infer_tags(path: Path, name: str, calls: set[str], strings: list[str]) -> list[str]:
    blob = " ".join([str(path), name, " ".join(calls), " ".join(strings)]).lower()
    tags = []
    checks = [
        ("m5f_canonical", ["m5f", "canonical"]), ("observation_not_canonical", ["observation", "canonical"]),
        ("bounded_watchlist", ["bounded", "watchlist"]), ("no_full_market_scan", ["full_market_scan", "full-market", "target_universe"]),
        ("no_trading_semantics", ["buy", "sell", "hold", "recommendation", "target price", "ranking"]),
        ("raw_payload_leakage", ["raw payload", "raw_payload"]), ("frontend_public_write", ["frontend", "public"]),
        ("research_generated_write", ["research/generated", "generated"]), ("production_prod_write", ["prod", "production"]),
        ("ssl_policy", ["ssl_policy", "tls", "compatibility", "unsafe"]), ("invalid_ssl_fail_closed", ["invalid", "ssl_policy", "fail"]),
        ("fastapi_execute_confirmation", ["fastapi", "execute", "confirmation"]), ("mcp_fail_closed", ["mcp", "fail"]),
        ("source_health", ["source_health", "m5q"]), ("conversation_context", ["conversation", "m5n", "context pack"]),
        ("m6e_acceptance", ["m6e"]), ("m6g_browser_e2e", ["m6g", "browser", "playwright"]),
        ("frontend_static_contract", ["frontend", "static", "contract"]), ("snapshot_schema", ["snapshot", "schema"]),
        ("briefing_render", ["briefing", "markdown"]), ("ai_context_pack", ["ai context", "context_pack"]),
        ("m5b_staging", ["m5b", "staging"]), ("m5c_staging", ["m5c", "rollback", "promotion"]),
        ("m5e_publication", ["m5e", "publication"]), ("governance_path", ["forbidden_path", "governance"]),
        ("forbidden_behavior", ["forbidden_behavior", "forbidden behavior"]),
    ]
    for tag, needles in checks:
        if any(n in blob for n in needles):
            tags.append(tag)
    return tags or ["unknown"]


def analyze_file(path: Path, root: Path, include_assertions: bool) -> list[TestRow]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imps = imports(tree)
    rows = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test_"):
            continue
        decs = [decorator_name(d) for d in node.decorator_list]
        markers = [d for d in decs if d.startswith("pytest.mark") or ".parametrize" in d]
        param_decs = [d for d in node.decorator_list if "parametrize" in decorator_name(d)]
        case_est = 0
        for d in param_decs:
            if isinstance(d, ast.Call) and len(d.args) >= 2 and isinstance(d.args[1], (ast.List, ast.Tuple)):
                case_est += len(d.args[1].elts)
        calls = {call_name(n.func) or "" for n in ast.walk(node) if isinstance(n, ast.Call)}
        asserts = [n for n in ast.walk(node) if isinstance(n, ast.Assert)]
        assertion_texts = [unparse(a.test) for a in asserts]
        strings = const_strings(node)
        tags = infer_tags(path.resolve().relative_to(root.resolve()), node.name, calls, strings)
        fp = "|".join(sorted(assertion_texts))
        taut = any(" or True" in t or t.strip() == "True" for t in assertion_texts)
        key_base = tags[0]
        if taut:
            cluster = f"{key_base}:tautological_assertion"
        elif fp:
            cluster = f"{key_base}:assert:{hashlib.sha256(fp.encode()).hexdigest()[:12]}"
        else:
            cluster = f"{key_base}:no_assert:{';'.join(sorted(calls))[:80]}"
        owner = next((OWNER_HINTS[t] for t in tags if t in OWNER_HINTS), "")
        action = "preserve_unique" if any(t in SAFETY_CRITICAL for t in tags) else ("candidate_duplicate" if taut else "defer_manual_review")
        rows.append(TestRow({
            "test_file": str(path.resolve().relative_to(root.resolve())), "test_function": node.name, "line_number": str(node.lineno),
            "decorators": csv_join(decs), "pytest_markers": csv_join(markers), "is_parametrized": str(bool(param_decs)).lower(),
            "parametrize_case_count_estimate": str(case_est), "imported_modules": csv_join(imps), "called_functions": csv_join(calls),
            "assert_count": str(len(asserts)), "assertion_keyword_summary": (" | ".join(assertion_texts)[:300] if include_assertions else csv_join([w for w in ["equals" if "==" in fp else "", "contains" if " in " in fp else "", "truthy" if fp else ""]])),
            "string_constant_summary": " | ".join(strings[:8])[:300], "risk_tags": csv_join(tags), "risk_cluster_key": cluster,
            "likely_authoritative_owner": owner, "recommended_review_action": action, "notes": "static_analysis_advisory" + (";tautological_assertion" if taut else ""),
        }, fp, taut))
    return rows


def build_clusters(rows: list[TestRow]) -> list[dict[str, str]]:
    groups = defaultdict(list)
    for r in rows:
        groups[r.values["risk_cluster_key"]].append(r)
    out = []
    for key, items in sorted(groups.items()):
        tags = csv_join(t for r in items for t in r.values["risk_tags"].split(";") if t)
        owner = next((r.values["likely_authoritative_owner"] for r in items if r.values["likely_authoritative_owner"]), "")
        critical = any(t in SAFETY_CRITICAL for t in tags.split(";"))
        exact_dup = (
            len(items) > 1
            and len({r.assertion_fingerprint for r in items}) == 1
            and items[0].assertion_fingerprint
            and len({r.values["called_functions"] for r in items}) == 1
        )
        taut = all(r.tautological for r in items)
        if owner and not critical and (taut or exact_dup):
            guess, safe, reason = "true", "yes", "tautological or exact duplicate assertion with explicit non-critical owner"
        elif len(items) > 1:
            guess, safe, reason = "partial", "manual_review_required", "static cluster overlap needs human semantic review"
        else:
            guess, safe, reason = "unclear", "no", "single test or no duplicate evidence"
        sorted_items = sorted(items, key=lambda r: (r.values["test_file"], int(r.values["line_number"])))
        out.append({
            "risk_cluster_key": key, "risk_tags": tags, "cluster_size": str(len(items)),
            "candidate_owner": owner or (f"{sorted_items[0].values['test_file']}::{sorted_items[0].values['test_function']}" if sorted_items else ""),
            "candidate_duplicates": csv_join(f"{r.values['test_file']}::{r.values['test_function']}" for r in sorted_items[1:]),
            "semantic_equivalence_guess": guess, "safe_to_auto_retire": safe, "reason": reason,
        })
    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tests-dir", default="tests")
    p.add_argument("--output-dir", default="docs/reviews/m6j_r2_inventory")
    p.add_argument("--format", choices=["csv"], default="csv")
    p.add_argument("--include-assertion-snippets", action="store_true")
    args = p.parse_args()
    root = Path.cwd(); tests_dir = Path(args.tests_dir); outdir = Path(args.output_dir); outdir.mkdir(parents=True, exist_ok=True)
    rows: list[TestRow] = []
    for path in sorted(tests_dir.rglob("test_*.py")):
        rows.extend(analyze_file(path, root, args.include_assertion_snippets))
    clusters = build_clusters(rows)
    with (outdir/"test_function_inventory.csv").open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=INVENTORY_COLUMNS); w.writeheader(); w.writerows([r.values for r in rows])
    with (outdir/"duplicate_risk_clusters.csv").open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=CLUSTER_COLUMNS); w.writeheader(); w.writerows(clusters)
    tag_counts = Counter(t for r in rows for t in r.values["risk_tags"].split(";") if t)
    largest = sorted(clusters, key=lambda c: int(c["cluster_size"]), reverse=True)[:10]
    safe = [c for c in clusters if c["safe_to_auto_retire"] == "yes"]
    manual = [c for c in clusters if c["safe_to_auto_retire"] == "manual_review_required"]
    summary = ["# M6J-R2 Test Risk Inventory Summary", "", "Static analysis is advisory and does not prove semantic equivalence by itself.", "", f"- Test functions detected: {len(rows)}", f"- Duplicate clusters detected: {len(clusters)}", f"- safe_to_auto_retire clusters: {len(safe)}", f"- manual_review_required clusters: {len(manual)}", "", "## Risk tag distribution"]
    summary += [f"- {k}: {v}" for k,v in tag_counts.most_common()]
    summary += ["", "## Largest duplicate-risk clusters"]
    summary += [f"- {c['risk_cluster_key']} ({c['cluster_size']}): {c['reason']}" for c in largest]
    (outdir/"summary.md").write_text("\n".join(summary)+"\n", encoding="utf-8")
    print(f"Wrote {len(rows)} test functions to {outdir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
