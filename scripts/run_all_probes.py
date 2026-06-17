import json
import os
from datetime import datetime, timezone

from probe_twse_openapi import probe as probe_twse
from probe_tpex_openapi import probe as probe_tpex
from probe_yahoo import probe as probe_yahoo
from probe_twse_mis import probe as probe_mis
from probe_finmind import probe as probe_finmind
from probe_fugle_fubon import probe as probe_fugle_fubon

def get_abs_path(relative_path):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, relative_path)

def load_targets():
    targets_path = get_abs_path("config/market_targets.json")
    try:
        with open(targets_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load targets from {targets_path}. Using fallbacks. Error: {e}")
        return None

def extract_symbols(targets, key_type):
    if not targets:
        return []
    symbols = []
    for group_key, group_data in targets.items():
        # Depending on the source, we might not query everything, but we gather them
        symbols.extend(group_data.get("symbols", {}).get(key_type, []))
    # Filter empty and duplicates
    return list(dict.fromkeys(filter(None, symbols)))

def extract_finmind_datasets(targets):
    if not targets:
        return []
    datasets = []
    for group_key, group_data in targets.items():
        syms = group_data.get("symbols", {}).get("standard", [])
        for sym in syms:
            if group_key == "futures":
                datasets.append(("TaiwanFutureDaily", sym))
            elif group_key == "funds":
                # For demonstration, skip funds or map to something specific if known
                pass
            elif sym == "TAIEX":
                datasets.append(("TaiwanStockPrice", sym))
            else:
                datasets.append(("TaiwanStockPrice", sym))
    return datasets

def generate_reports(results):
    os.makedirs(get_abs_path("docs"), exist_ok=True)
    os.makedirs(get_abs_path("research/generated"), exist_ok=True)
    os.makedirs(get_abs_path("frontend/public"), exist_ok=True)

    flat_results = []
    for r in results:
        if isinstance(r, list):
            flat_results.extend(r)
        else:
            flat_results.append(r)

    # 1. Capability Matrix (Markdown)
    with open(get_abs_path("docs/capability_matrix.md"), "w", encoding="utf-8") as f:
        f.write("# Data Source Capability Matrix\n\n")
        f.write("| Source | Source Type | URL/Endpoint | Auth | Session | Probe Status | HTTP | Parse | Norm | Freshness | Delay | Risk | AI Suitability | Usable Now | Unsupported | Failed | Notes | Last Verified |\n")
        f.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
        for res in flat_results:
            c_stat = res.get('contract_status', 'unknown')
            auth = "Yes" if res.get('requires_auth') else "No"
            sess = "Yes" if res.get('requires_session') else "No"
            unsupported = len(res.get('unsupported_targets', []))
            failed = len(res.get('failed_targets', []))
            usable = "Yes" if res.get('is_usable_now') else "No"

            f.write(f"| {res['source']} | {res['source_type']} | {res['request']['url']} | {auth} | {sess} | `{c_stat}` | {res.get('http_status')} | {res.get('parse_status')} | {res.get('normalization_status')} | {res.get('freshness_status')} | {res.get('delay_status')} | {res.get('risk_level')} | {res.get('ai_suitability')} | **{usable}** | {unsupported} | {failed} | {', '.join(res.get('risk_notes', []))} | {res.get('retrieved_at_utc')} |\n")

    # 2. Source Catalog (Markdown)
    with open(get_abs_path("docs/source_catalog.md"), "w", encoding="utf-8") as f:
        f.write("# Data Source Catalog\n\n")
        f.write("Generated automatically by probes. Details specific source capabilities.\n\n")
        for res in flat_results:
            f.write(f"## {res['source']}\n\n")
            f.write(f"- **Type:** {res['source_type']}\n")
            f.write(f"- **URL:** {res['request']['url']}\n")
            f.write(f"- **Contract Status:** `{res['contract_status']}`\n")
            f.write(f"- **Usable Now:** {res.get('is_usable_now')}\n")
            f.write(f"- **Potentially Usable (Creds):** {res.get('potentially_usable_with_credentials')}\n")
            f.write(f"- **AI Suitability:** {res.get('ai_suitability')}\n")
            f.write(f"- **Delay Status:** {res.get('delay_status')}\n")
            if res.get('staleness_seconds') is not None:
                f.write(f"- **Staleness:** {res.get('staleness_seconds')} seconds\n")
            if res.get('errors'):
                f.write(f"- **Errors:** {', '.join(res.get('errors'))}\n")
            if res.get('warnings'):
                f.write(f"- **Warnings:** {', '.join(res.get('warnings'))}\n")
            if res.get('unsupported_targets'):
                f.write(f"- **Unsupported targets:** {', '.join(res.get('unsupported_targets'))}\n")
            if res.get('failed_targets'):
                f.write(f"- **Failed targets:** {', '.join(res.get('failed_targets'))}\n")
            f.write("\n")

    # 3. Probe Log (Markdown)
    with open(get_abs_path("research/probe_log.md"), "w", encoding="utf-8") as f:
        f.write("# Probe Execution Log\n\n")
        f.write(f"Last Run: {datetime.now(timezone.utc).isoformat()}\n\n")
        for res in flat_results:
            f.write(f"## {res['source']} ({res['probe_id']})\n")
            f.write(f"- Contract Status: `{res['contract_status']}`\n")
            f.write(f"- HTTP Status: {res['http_status']}\n")
            if res.get("errors"):
                f.write(f"- Errors: {', '.join(res.get('errors'))}\n")
            f.write("\n")

    # 4. Frontend Matrix (JSON)
    with open(get_abs_path("frontend/public/matrix.json"), "w", encoding="utf-8") as f:
        json.dump({
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "results": flat_results
        }, f, ensure_ascii=False, indent=2)

    # 5. AI Context Pack
    ai_context = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "Provide AI agents with up-to-date facts about available Taiwan equity market data sources.",
        "usable_sources": [r for r in flat_results if r.get('is_usable_now')],
        "official_sources": [r for r in flat_results if 'official' in r.get('source_type', '')],
        "unofficial_sources": [r for r in flat_results if 'unofficial' in r.get('source_type', '')],
        "auth_required_sources": [r for r in flat_results if r.get('potentially_usable_with_credentials')],
        "failed_or_doc_only_sources": [r for r in flat_results if r.get('contract_status') in ['failed', 'doc_only', 'blocked']],
        "guidelines": [
            "Never claim an 'unofficial_frontend_endpoint' is an official API.",
            "Do not hallucinate real-time capabilities if the delay_status is 'eod' or 'stale'.",
            "A source marked 'doc_only' or 'auth_required' without provided credentials cannot be used to fetch live data."
        ]
    }

    with open(get_abs_path("research/generated/ai_context_pack.json"), "w", encoding="utf-8") as f:
        json.dump(ai_context, f, ensure_ascii=False, indent=2)

    with open(get_abs_path("research/generated/ai_context_pack.md"), "w", encoding="utf-8") as f:
        f.write("# AI Context Pack\n\n")
        f.write(f"Generated at: {ai_context['generated_at']}\n\n")
        f.write("## Guidelines\n")
        for g in ai_context['guidelines']:
            f.write(f"- {g}\n")
        f.write("\n## Usable Sources Now\n")
        for s in ai_context['usable_sources']:
             f.write(f"- **{s['source']}** ({s['source_type']}): `{s['contract_status']}`\n")

if __name__ == "__main__":
    targets = load_targets()

    yahoo_symbols = extract_symbols(targets, "yahoo")
    mis_symbols = extract_symbols(targets, "twse_mis")
    finmind_datasets = extract_finmind_datasets(targets)

    results = []
    print("Running probes...")

    # Run official probes (no custom targets needed usually, they fetch all)
    try:
        results.append(probe_twse())
    except Exception as e:
        print(f"Error running TWSE probe: {e}")

    try:
        results.append(probe_tpex())
    except Exception as e:
         print(f"Error running TPEx probe: {e}")

    # Run parameterised probes
    try:
        results.append(probe_yahoo(symbols=yahoo_symbols))
    except Exception as e:
        print(f"Error running Yahoo probe: {e}")

    try:
        results.append(probe_mis(symbols=mis_symbols))
    except Exception as e:
        print(f"Error running TWSE MIS probe: {e}")

    try:
        results.append(probe_finmind(datasets=finmind_datasets))
    except Exception as e:
         print(f"Error running FinMind probe: {e}")

    # Run doc-only probes
    try:
        results.append(probe_fugle_fubon())
    except Exception as e:
        print(f"Error running doc-only probes: {e}")

    print("Generating reports...")
    generate_reports(results)
    print("Done.")
