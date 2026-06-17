import json
import os
from datetime import datetime

from probe_twse_openapi import probe as probe_twse
from probe_tpex_openapi import probe as probe_tpex
from probe_yahoo import probe as probe_yahoo
from probe_twse_mis import probe as probe_mis
from probe_finmind import probe as probe_finmind
from probe_fugle_fubon import probe as probe_fugle_fubon

def get_abs_path(relative_path):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, relative_path)

def generate_reports(results):
    os.makedirs(get_abs_path("docs"), exist_ok=True)
    os.makedirs(get_abs_path("research"), exist_ok=True)
    os.makedirs(get_abs_path("frontend/public"), exist_ok=True)

    flat_results = []
    for r in results:
        if isinstance(r, list):
            flat_results.extend(r)
        else:
            flat_results.append(r)

    with open(get_abs_path("docs/capability_matrix.md"), "w", encoding="utf-8") as f:
        f.write("# Data Source Capability Matrix\n\n")
        f.write("| Source | Type | Endpoint/URL | Success | Note |\n")
        f.write("|---|---|---|---|---|\n")
        for res in flat_results:
            success_mark = "✅" if res.get("success") else "❌"
            f.write(f"| {res['source']} | API/Doc | {res['url']} | {success_mark} | Status: {res['status']} |\n")

    with open(get_abs_path("docs/source_catalog.md"), "w", encoding="utf-8") as f:
        f.write("# Data Source Catalog\n\n")
        f.write("Generated automatically by probes.\n\n")
        f.write("| Source | URL | Status | Success |\n")
        f.write("|---|---|---|---|\n")
        for res in flat_results:
            success_mark = "✅" if res.get("success") else "❌"
            f.write(f"| {res['source']} | {res['url']} | {res['status']} | {success_mark} |\n")

    with open(get_abs_path("research/probe_log.md"), "w", encoding="utf-8") as f:
        f.write("# Probe Execution Log\n\n")
        f.write(f"Last Run: {datetime.now().isoformat()}\n\n")
        for res in flat_results:
            f.write(f"## {res['source']}\n")
            f.write(f"- URL: {res['url']}\n")
            f.write(f"- Status: {res['status']}\n")
            f.write(f"- Success: {res.get('success')}\n")
            if "details" in res:
                f.write(f"- Details: {json.dumps(res['details'], ensure_ascii=False)}\n")
            if "error" in res:
                f.write(f"- Error: {res['error']}\n")
            f.write("\n")

    with open(get_abs_path("frontend/public/matrix.json"), "w", encoding="utf-8") as f:
        json.dump({
            "last_updated": datetime.now().isoformat(),
            "results": flat_results
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    results = []
    print("Running probes...")
    results.append(probe_twse())
    results.append(probe_tpex())

    yahoo_symbols = ["2330.TW", "1435.TW", "0050.TW", "00929.TW", "^TWII", "TWD=X"]
    results.append(probe_yahoo(symbols=yahoo_symbols))

    mis_symbols = ["tse_2330.tw", "tse_1435.tw", "tse_0050.tw", "tse_00929.tw", "tse_t00.tw", "otc_o00.tw"]
    results.append(probe_mis(symbols=mis_symbols))

    finmind_datasets = [
        ("TaiwanStockPrice", "2330"),
        ("TaiwanStockPrice", "1435"),
        ("TaiwanStockPrice", "0050"),
        ("TaiwanStockPrice", "00929"),
        ("TaiwanStockPrice", "TAIEX"),
        ("TaiwanFutureDaily", "TX"),
    ]
    results.append(probe_finmind(datasets=finmind_datasets))

    results.append(probe_fugle_fubon())

    print("Generating reports...")
    generate_reports(results)
    print("Done.")
