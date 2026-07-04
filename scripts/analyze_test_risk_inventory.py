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
    "review_priority","review_score","member_files","unique_called_targets",
    "unique_assertion_shapes","owner_confidence",
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


def clean_cell(value: object) -> str:
    return str(value).strip()


def csv_join(items: Iterable[str]) -> str:
    return ";".join(sorted({clean_cell(i) for i in items if clean_cell(i)}))


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



def normalized_tokens(*parts: str) -> set[str]:
    text = " ".join(parts).lower().replace("-", "_").replace("/", " ")
    for ch in "()[]{}.,:;='\"|":
        text = text.replace(ch, " ")
    return {token for token in text.split() if token}


def contains_any(text: str, needles: Iterable[str]) -> bool:
    lowered = text.lower().replace("-", "_")
    return any(needle in lowered for needle in needles)


def infer_tags(
    path: Path,
    name: str,
    calls: set[str],
    strings: list[str],
    assertion_texts: list[str] | None = None,
) -> list[str]:
    """Infer risk tags using rule-based evidence scoring.

    Rules require multi-part evidence instead of broad keyword OR matching. This
    intentionally favors precision over recall because the analyzer feeds human
    retirement review.
    """
    path_text = str(path).lower()
    name_text = name.lower()
    calls_text = " ".join(sorted(calls)).lower()
    strings_text = " ".join(strings).lower()
    asserts_text = " ".join(assertion_texts or []).lower()
    identity_text = " ".join([path_text, name_text, calls_text])
    evidence_text = " ".join([calls_text, strings_text, asserts_text])
    all_text = " ".join([identity_text, evidence_text]).replace("-", "_")
    tags: list[str] = []

    def add(tag: str, condition: bool) -> None:
        if condition:
            tags.append(tag)

    has_mcp = contains_any(identity_text, ["mcp", "mcp_server"])
    fail_evidence = contains_any(evidence_text, ["fail_closed", "fails_closed", "rejected", "reject", "error", "status", "400", "http_exception", "httpexception"])
    add("mcp_fail_closed", has_mcp and fail_evidence)

    has_ssl = contains_any(all_text, ["ssl_policy", "tls", "ssl"])
    invalid_evidence = contains_any(all_text, ["invalid", "unsupported", "bad_ssl", "bad tls"])
    ssl_fail_evidence = contains_any(evidence_text, ["fail_closed", "fails_closed", "400", "valueerror", "httpexception", "http_exception", "rejected", "reject", "error"])
    add("invalid_ssl_fail_closed", has_ssl and invalid_evidence and ssl_fail_evidence)
    add("ssl_policy", has_ssl and not (has_ssl and invalid_evidence and ssl_fail_evidence))

    add("frontend_public_write", "frontend/public" in str(path).lower() or "frontend/public" in strings_text or (contains_any(all_text, ["frontend"]) and contains_any(all_text, ["write", "output", "destination"])))
    add("frontend_static_contract", contains_any(all_text, ["frontend"]) and contains_any(all_text, ["static", "contract", "html", " js", ".js", "token"]))

    add("m5f_canonical", contains_any(all_text, ["m5f", "canonical_market_context", "canonical package"]))
    add("observation_not_canonical", contains_any(all_text, ["observation"]) and contains_any(all_text, ["not canonical", "canonical"]))
    add("bounded_watchlist", contains_any(all_text, ["bounded_watchlist", "bounded watchlist", "watchlist"]) and contains_any(all_text, ["bounded", "default_watchlist", "target_count", "symbols"]))
    add("no_full_market_scan", contains_any(all_text, ["full_market_scan", "full market", "target_universe"]) and contains_any(all_text, ["false", "reject", "fails", "blocked", "bounded"]))
    add("no_trading_semantics", contains_any(all_text, ["trading_signal", "buy_sell_hold", "recommendation", "target price", "ranking"]) and contains_any(all_text, ["forbidden", "absent", "reject", "no_trading", "must_not"]))
    add("raw_payload_leakage", contains_any(all_text, ["raw_payload", "raw payload", "raw_field_sample"]) and contains_any(all_text, ["leak", "omits", "absent", "forbidden", "does_not_expose", "no_raw"]))
    add("research_generated_write", contains_any(all_text, ["research/generated"]) or (contains_any(all_text, ["research", "generated"]) and contains_any(all_text, ["write", "output", "destination"])))
    add("production_prod_write", contains_any(all_text, ["production", "prod"]) and contains_any(all_text, ["write", "output", "destination", "forbidden", "reject"]))
    add("fastapi_execute_confirmation", contains_any(all_text, ["fastapi", "testclient", "api/"]) and contains_any(all_text, ["execute", "confirmation", "confirm_execute"]))
    add("source_health", contains_any(all_text, ["source_health", "m5q", "health report"]) and contains_any(all_text, ["health", "degraded", "healthy", "failed", "unsupported", "source"]))
    add("conversation_context", contains_any(all_text, ["conversation", "m5n", "context pack", "context_package"]) and contains_any(all_text, ["context", "handoff", "markdown", "package"]))
    add("m6e_acceptance", contains_any(all_text, ["m6e", "operator_acceptance"]))
    add("m6g_browser_e2e", contains_any(all_text, ["m6g", "browser", "playwright", "e2e"]) and contains_any(all_text, ["browser", "playwright", "e2e", "chromium"]))
    add("snapshot_schema", contains_any(all_text, ["snapshot"]) and contains_any(all_text, ["schema", "symbol", "source_health", "failed_source"]))
    add("briefing_render", contains_any(all_text, ["briefing"]) and contains_any(all_text, ["render", "markdown", "table", "heading"]))
    add("ai_context_pack", contains_any(all_text, ["ai_context", "ai context", "context_pack"]) and contains_any(all_text, ["pack", "markdown", "json", "summary"]))
    add("m5b_staging", contains_any(all_text, ["m5b"]) and contains_any(all_text, ["staging", "authorization", "controlled_live", "execution_scope"]))
    add("m5c_staging", contains_any(all_text, ["m5c"]) and contains_any(all_text, ["staging", "promotion", "rollback"]))
    add("m5e_publication", contains_any(all_text, ["m5e"]) and contains_any(all_text, ["publication", "frontend", "candidate", "transaction"]))
    add("governance_path", contains_any(all_text, ["governance", "forbidden_path", "forbidden path"]) and contains_any(all_text, ["path", "guard", "forbidden", "changed_files"]))
    add("forbidden_behavior", contains_any(all_text, ["forbidden_behavior", "forbidden behavior"]) or (contains_any(all_text, ["forbidden"]) and contains_any(all_text, ["scanner", "behavior"])))

    return tags or ["unknown"]


def normalize_called_target(calls: set[str]) -> str:
    meaningful = sorted(c for c in calls if c and c not in {"str", "len", "bool", "dict", "list", "set"})
    if not meaningful:
        return "no_call"
    preferred = [c for c in meaningful if not c.startswith(("pytest.", "Path", "json."))]
    target = (preferred or meaningful)[0]
    return target.lower().replace(".", "_")[:80]


def normalize_assertion_shape(assertion_texts: list[str], tautological: bool) -> str:
    if tautological:
        return "tautological"
    if not assertion_texts:
        return "no_assert"
    shapes: list[str] = []
    for text in assertion_texts:
        lowered = text.lower()
        if "==" in lowered:
            shapes.append("equals")
        elif "!=" in lowered:
            shapes.append("not_equals")
        elif " in " in lowered:
            shapes.append("contains")
        elif "not in" in lowered:
            shapes.append("not_contains")
        elif "raises" in lowered:
            shapes.append("raises")
        elif " is false" in lowered or " is true" in lowered:
            shapes.append("boolean_identity")
        else:
            shapes.append("truthy")
    return "+".join(sorted(set(shapes)))[:80]

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
        fp = "|".join(sorted(assertion_texts))
        taut = any(" or True" in t or t.strip() == "True" for t in assertion_texts)
        tags = infer_tags(path.resolve().relative_to(root.resolve()), node.name, calls, strings, assertion_texts)
        primary_risk_id = tags[0]
        normalized_target = normalize_called_target(calls)
        assertion_shape = normalize_assertion_shape(assertion_texts, taut)
        cluster = f"{primary_risk_id}:{normalized_target}:{assertion_shape}"
        owner = next((OWNER_HINTS[t] for t in tags if t in OWNER_HINTS), "")
        action = "preserve_unique" if any(t in SAFETY_CRITICAL for t in tags) else ("candidate_duplicate" if taut else "defer_manual_review")
        row_values = {
            "test_file": str(path.resolve().relative_to(root.resolve())), "test_function": node.name, "line_number": str(node.lineno),
            "decorators": csv_join(decs), "pytest_markers": csv_join(markers), "is_parametrized": str(bool(param_decs)).lower(),
            "parametrize_case_count_estimate": str(case_est), "imported_modules": csv_join(imps), "called_functions": csv_join(calls),
            "assert_count": str(len(asserts)), "assertion_keyword_summary": (" | ".join(assertion_texts)[:300] if include_assertions else csv_join([w for w in ["equals" if "==" in fp else "", "contains" if " in " in fp else "", "truthy" if fp else ""]])),
            "string_constant_summary": " | ".join(strings[:8])[:300], "risk_tags": csv_join(tags), "risk_cluster_key": cluster,
            "likely_authoritative_owner": owner, "recommended_review_action": action, "notes": "static_analysis_advisory" + (";tautological_assertion" if taut else ""),
        }
        rows.append(TestRow({key: clean_cell(value) for key, value in row_values.items()}, fp, taut))
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
        member_files = {r.values["test_file"] for r in items}
        called_targets = {r.values["risk_cluster_key"].split(":", 2)[1] if ":" in r.values["risk_cluster_key"] else "" for r in items}
        assertion_shapes = {r.values["risk_cluster_key"].rsplit(":", 1)[-1] for r in items}
        risk_tag_sets = {r.values["risk_tags"] for r in items}
        text_blob = " ".join(
            [key, tags]
            + [r.values["test_file"] for r in items]
            + [r.values["test_function"] for r in items]
            + [r.values["called_functions"] for r in items]
            + [r.values["assertion_keyword_summary"] for r in items]
        ).lower()
        safety_penalty_terms = [
            "failure_injection", "rollback", "crash", "tamper", "tls precedence",
            "browser", "m6g", "m6e", "ssl_policy", "invalid_ssl_fail_closed",
            "mcp_fail_closed", "governance_path", "forbidden_behavior", "m5f_canonical",
        ]
        score = len(items)
        if len(called_targets) == 1:
            score += 3
        if len(assertion_shapes) == 1:
            score += 3
        if len(risk_tag_sets) == 1:
            score += 2
        if owner:
            score += 2
        if any(marker in text_blob for marker in ["m3g", "m4", "m5a", "m5b", "m5c", "m5d", "m5e", "m5f", "m5k", "m5n", "m6a", "m6b", "m6d"]):
            score += 1
        if critical or any(term in text_blob for term in safety_penalty_terms):
            score -= 6
        if any(term in text_blob for term in ["failure_injection", "rollback", "crash", "tamper", "tls precedence", "browser e2e"]):
            score -= 4
        if score >= 13 and len(items) > 1 and not critical:
            priority = "P0"
        elif score >= 9 and len(items) > 1 and not critical:
            priority = "P1"
        elif score >= 5 and len(items) > 1:
            priority = "P2"
        else:
            priority = "P3"
        owner_confidence = "high" if owner and len(risk_tag_sets) == 1 else ("medium" if owner else "low")
        out.append({
            "risk_cluster_key": key, "risk_tags": tags, "cluster_size": str(len(items)),
            "candidate_owner": owner or (f"{sorted_items[0].values['test_file']}::{sorted_items[0].values['test_function']}" if sorted_items else ""),
            "candidate_duplicates": csv_join(f"{r.values['test_file']}::{r.values['test_function']}" for r in sorted_items[1:]),
            "semantic_equivalence_guess": guess, "safe_to_auto_retire": safe, "reason": reason,
            "review_priority": priority, "review_score": str(score),
            "member_files": csv_join(member_files),
            "unique_called_targets": csv_join(called_targets),
            "unique_assertion_shapes": csv_join(assertion_shapes),
            "owner_confidence": owner_confidence,
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
        w=csv.DictWriter(f, fieldnames=INVENTORY_COLUMNS, lineterminator="\n"); w.writeheader(); w.writerows([r.values for r in rows])
    with (outdir/"duplicate_risk_clusters.csv").open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=CLUSTER_COLUMNS, lineterminator="\n"); w.writeheader(); w.writerows(clusters)
    tag_counts = Counter(t for r in rows for t in r.values["risk_tags"].split(";") if t)
    largest = sorted(clusters, key=lambda c: int(c["cluster_size"]), reverse=True)[:10]
    safe = [c for c in clusters if c["safe_to_auto_retire"] == "yes"]
    manual = [c for c in clusters if c["safe_to_auto_retire"] == "manual_review_required"]
    priority_counts = Counter(c["review_priority"] for c in clusters)
    summary = ["# M6J-R2 Test Risk Inventory Summary", "", "Static analysis is advisory and does not prove semantic equivalence by itself.", "", f"- Test functions detected: {len(rows)}", f"- Duplicate clusters detected: {len(clusters)}", f"- safe_to_auto_retire clusters: {len(safe)}", f"- manual_review_required clusters: {len(manual)}", f"- P0 clusters: {priority_counts['P0']}", f"- P1 clusters: {priority_counts['P1']}", f"- P2 clusters: {priority_counts['P2']}", f"- P3 clusters: {priority_counts['P3']}", "", "## Risk tag distribution"]
    summary += [f"- {k}: {v}" for k,v in tag_counts.most_common()]
    summary += ["", "## Largest duplicate-risk clusters"]
    summary += [f"- {c['risk_cluster_key']} ({c['cluster_size']}): {c['reason']}" for c in largest]
    (outdir/"summary.md").write_text("\n".join(summary)+"\n", encoding="utf-8")
    print(f"Wrote {len(rows)} test functions to {outdir}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
